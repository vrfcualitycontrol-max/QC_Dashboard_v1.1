import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, MetaData, Table, select, delete, update
from sqlalchemy.orm import Session

# Add current directory to path so we can import normalize_name from parser
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from parser import normalize_name

def merge_crm_actions(dict1, dict2):
    res = (dict1 or {}).copy()
    for k, v in (dict2 or {}).items():
        if isinstance(v, (int, float)):
            res[k] = res.get(k, 0) + v
        else:
            res[k] = v
    return res

def merge_json_scores(dict1, dict2):
    res = (dict1 or {}).copy()
    for k, v in (dict2 or {}).items():
        if v:
            res[k] = v
    return res

def is_garbage_name(name):
    if not name:
        return True
    lower = name.lower().strip()
    if lower in ('admin', 'названия строк', 'количество по полю тип задачи', 'количество по полю тип зада'):
        return True
    if lower.startswith('за период:') or 'промежуточный отчет' in lower:
        return True
    return False

def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("[ERROR] DATABASE_URL env var not set!")
        sys.exit(1)
        
    engine = create_engine(db_url)
    metadata = MetaData()
    employee_scores = Table("employee_scores", metadata, autoload_with=engine)
    
    with Session(engine) as session:
        # 1. Delete garbage records
        print("Purging garbage records...")
        stmt_select_all = select(employee_scores)
        rows = session.execute(stmt_select_all).fetchall()
        
        deleted_count = 0
        for row in rows:
            if is_garbage_name(row.employee_name):
                session.execute(delete(employee_scores).where(employee_scores.c.id == row.id))
                deleted_count += 1
        
        print(f"Purged {deleted_count} garbage records.")
        session.commit()
        
        # Reload rows after delete
        rows = session.execute(stmt_select_all).fetchall()
        
        # Group rows by (normalized_name, month, period)
        grouped = {}
        for row in rows:
            norm_name = normalize_name(row.employee_name)
            
            # Additional double check: if normalized name is still invalid, skip or delete
            if is_garbage_name(norm_name):
                session.execute(delete(employee_scores).where(employee_scores.c.id == row.id))
                print(f"Deleted extra invalid normalized record: {row.employee_name}")
                continue
                
            key = (norm_name, row.month, row.period)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(row)
            
        print(f"Total unique groups found: {len(grouped)}")
        
        for (norm_name, month, period), records in grouped.items():
            if len(records) == 1:
                # Only one record in group, just check if we need to update its name to normalized
                row = records[0]
                if row.employee_name != norm_name:
                    session.execute(
                        update(employee_scores)
                        .where(employee_scores.c.id == row.id)
                        .values(employee_name=norm_name, updated_at=datetime.now(timezone.utc))
                    )
                    print(f"Updated name: '{row.employee_name}' -> '{norm_name}'")
            else:
                # Multiple records! We must merge them into one and delete the rest
                print(f"Merging {len(records)} records for '{norm_name}' ({month}, {period})...")
                
                # We pick the "primary" record. Preferably one that already has TQS (Cyrillic Quality sheet)
                records_sorted = sorted(
                    records, 
                    key=lambda r: (1 if r.tqs and r.tqs > 0 else 0, 1 if r.employee_name == norm_name else 0),
                    reverse=True
                )
                primary = records_sorted[0]
                duplicates = records_sorted[1:]
                
                # Accumulate values
                merged_tqs = primary.tqs or 0.0
                merged_aht = primary.aht or "N/A"
                merged_activity = primary.activity_count or 0
                merged_svp = (primary.svp_scores or {}).copy()
                merged_raw = (primary.raw_scores or {}).copy()
                merged_tendencies = primary.tendencies or ""
                merged_rec = primary.recommendations or ""
                merged_collected_amount = primary.collected_amount or 0.0
                merged_collected_count = primary.collected_count or 0
                merged_collection_rate = primary.collection_rate or 0.0
                merged_plan_fulfillment = primary.plan_fulfillment or 0.0
                merged_crm_actions = (primary.crm_actions or {}).copy()
                merged_crm_summary = primary.crm_actions_summary or ""
                merged_crm_pattern = primary.crm_behavior_pattern or ""
                
                for dup in duplicates:
                    # TQS merge
                    if dup.tqs and dup.tqs > 0:
                        if merged_tqs > 0:
                            merged_tqs = (merged_tqs + dup.tqs) / 2.0
                        else:
                            merged_tqs = dup.tqs
                            
                    # AHT merge
                    if dup.aht and dup.aht != "N/A":
                        merged_aht = dup.aht
                        
                    # Sum activities and collections
                    merged_activity += dup.activity_count or 0
                    merged_collected_amount += dup.collected_amount or 0.0
                    merged_collected_count += dup.collected_count or 0
                    
                    # Merge JSONs
                    merged_svp = merge_json_scores(merged_svp, dup.svp_scores)
                    merged_raw = merge_json_scores(merged_raw, dup.raw_scores)
                    merged_crm_actions = merge_crm_actions(merged_crm_actions, dup.crm_actions)
                    
                    # Plan fulfillment
                    merged_plan_fulfillment = max(merged_plan_fulfillment, dup.plan_fulfillment or 0.0)
                    merged_collection_rate = max(merged_collection_rate, dup.collection_rate or 0.0)
                    
                    # Strings
                    if dup.tendencies and dup.tendencies not in merged_tendencies:
                        merged_tendencies = (merged_tendencies + "\n" + dup.tendencies).strip()
                    if dup.recommendations and dup.recommendations not in merged_rec:
                        merged_rec = (merged_rec + "\n" + dup.recommendations).strip()
                    if dup.crm_actions_summary and dup.crm_actions_summary not in merged_crm_summary:
                        merged_crm_summary = (merged_crm_summary + "\n" + dup.crm_actions_summary).strip()
                    if dup.crm_behavior_pattern:
                        merged_crm_pattern = dup.crm_behavior_pattern
                
                # Update primary record
                session.execute(
                    update(employee_scores)
                    .where(employee_scores.c.id == primary.id)
                    .values(
                        employee_name=norm_name,
                        tqs=merged_tqs,
                        aht=merged_aht,
                        activity_count=merged_activity,
                        svp_scores=merged_svp,
                        raw_scores=merged_raw,
                        tendencies=merged_tendencies,
                        recommendations=merged_rec,
                        collected_amount=merged_collected_amount,
                        collected_count=merged_collected_count,
                        collection_rate=merged_collection_rate,
                        plan_fulfillment=merged_plan_fulfillment,
                        crm_actions=merged_crm_actions,
                        crm_actions_summary=merged_crm_summary,
                        crm_behavior_pattern=merged_crm_pattern,
                        updated_at=datetime.now(timezone.utc)
                    )
                )
                
                # Delete duplicate records
                for dup in duplicates:
                    session.execute(delete(employee_scores).where(employee_scores.c.id == dup.id))
                    print(f"  Deleted duplicate ID {dup.id} ('{dup.employee_name}')")
                
        session.commit()
        print("Database cleanup and merging successfully completed!")

if __name__ == "__main__":
    main()
