# Dashboard SC v1.2.3 — Production Ready

## Release Info
- **Version:** 1.2.3
- **Release Date:** 20 апреля 2026 г.
- **Status:** ✅ Production Ready

## What's Fixed
This release fixes 6 critical bugs in operational indicators:

### 🐛 Bug Fixes
1. **Командный TQS**: 0.6% → 63.3%
   - Backend returns 0-1 format, frontend now multiplies by 100
   - All 23 employees correctly aggregated

2. **Progress Wave — Динамика среднего балла**
   - Now displays all 23 operator lines
   - Correct scale 0-100% on both axes
   - Works on both summary and detailed periods

3. **TQS по операторам — столбчатый график**
   - Bar chart now displays all employees
   - Correct 0-100% scale
   - Color coding: green (≥75%), yellow (60-74%), red (<60%)

4. **Приоритет «0»**
   - Now correctly counts operators with critical errors
   - Previously counted all zero values across all SVP criteria
   - Accurate representation of team risk level

5. **Зоны роста — анализ критических просадок**
   - TQS format: 0.29% → 29%
   - Recommendations populate correctly from backend
   - Both summary and detailed period views work

6. **Data Aggregation**
   - 0-1 format correctly converted to 0-100% for display
   - No data loss or corruption
   - Consistent across all components

## Testing
✅ KPI switches correctly when period changes  
✅ All graphs update properly  
✅ Data formatting matches requirements  
✅ New reporting periods (13-19.04.2026) loaded successfully  
✅ All operational indicators verified on:
  - Summary view (all periods)
  - Individual periods (01-05, 06-12, 13-19, etc.)

## Technical Details
- **Files Changed:** index.html (6 lines modified)
- **Lines:** 19315, 19406, 19437, 19497, 19573, priority logic
- **No Breaking Changes:** All existing functionality preserved

## Deployment
```bash
# Docker
docker build -t dashboard-sc:v1.2.3 .
docker-compose up -d

# Or use pre-built image
docker pull dashboard-sc:latest
```

## Backend Status
- PostgreSQL: ✅ Healthy
- FastAPI: ✅ Running (localhost:8000)
- nginx: ✅ Reverse proxy working

## Notes for Team Leads
- Dashboard now accurately reflects team performance metrics
- Use "Приоритет «0»" to identify operators needing intervention
- "Зоны роста" section provides targeted recommendations
- All historical data properly aggregated since February 2026
