// ============================================
// АНАЛИТИКА v1.2 FIX v3 — Chart.js + R² + динамические списки
// ============================================

const MONTH_ORDER={'Янв':1,'Фев':2,'Мар':3,'Апр':4,'Май':5,'Июн':6,'Июл':7,'Авг':8,'Сен':9,'Окт':10,'Ноя':11,'Дек':12};
function parsePeriodKey(p){const m=p.match(/(\d{2})-(\d{2})\s+(\w+)\s+(\d{4})/);return m?[parseInt(m[4]),MONTH_ORDER[m[3]]||0,parseInt(m[2])]:[0,0,0];}
function sortPeriodsDesc(periods){return[...periods].sort((a,b)=>{const ka=parsePeriodKey(a),kb=parsePeriodKey(b);for(let i=0;i<3;i++){if(kb[i]!==ka[i])return kb[i]-ka[i];}return 0;});}
function formatAHT(minutes){
    if(!minutes||minutes<=0)return'—';
    const mins=Math.floor(minutes);
    const secs=Math.round((minutes-mins)*60);
    return`${mins}:${secs.toString().padStart(2,'0')}`;
}

/** Переключение вкладок */
function switchAnalyticsTab(tabName){
    document.querySelectorAll('.analytics-content').forEach(el=>el.style.display='none');
    document.querySelectorAll('.analytics-tab').forEach(el=>{el.style.background='rgba(255,255,255,0.05)';el.style.color='var(--text-muted)';});
    document.getElementById(`analytics-${tabName}`).style.display='block';
    event.target.style.background='rgba(255,255,255,0.1)';event.target.style.color='var(--text-primary)';
    if(tabName==='history')loadEmployeeHistory();
    if(tabName==='trends')loadTrendsForecast();
    if(tabName==='compare')populateComparisonPeriods();
}

/** История сотрудника */
async function loadEmployeeHistory(){
    const select=document.getElementById('historyEmployeeSelect');
    const modeSelect=document.getElementById('historyModeSelect');
    const empName=select.value;
    const mode=modeSelect?.value||'detailed';
    if(!empName){document.getElementById('historyContent').innerHTML='<p style="text-align:center;color:var(--text-muted);">Выберите сотрудника</p>';return;}
    document.getElementById('historyContent').innerHTML='<p style="text-align:center;">Загрузка...</p>';
    try{
        const res=await fetch(`/api/history/${encodeURIComponent(empName)}?mode=${mode}`);
        const data=await res.json();
        if(data.error){document.getElementById('historyContent').innerHTML=`<p style="text-align:center;color:var(--danger);">${data.error}</p>`;return;}
        const modeLabel=mode==='summary'?'📊 Совокупный (по месяцам)':'📋 Детальный (по неделям)';
        let html=`<h4 style="margin-bottom:5px;">📜 ${empName}</h4><p style="color:var(--text-muted);margin-bottom:15px;font-size:0.85rem;">${modeLabel} — ${data.periods_count} записей</p><div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.9rem;"><thead><tr style="background:rgba(0,0,0,0.2);"><th style="padding:10px;border:1px solid var(--card-border);">Период</th><th style="padding:10px;border:1px solid var(--card-border);">TQS</th><th style="padding:10px;border:1px solid var(--card-border);">AHT</th><th style="padding:10px;border:1px solid var(--card-border);">Звонков</th></tr></thead><tbody>`;
        for(const h of data.history){
            const c=h.tqs>=0.75?'var(--success)':(h.tqs>=0.5?'var(--warning)':'var(--danger)');
            html+=`<tr><td style="padding:10px;border:1px solid var(--card-border);">${h.period}</td><td style="padding:10px;border:1px solid var(--card-border);color:${c};font-weight:700;">${(h.tqs*100).toFixed(1)}%</td><td style="padding:10px;border:1px solid var(--card-border);font-variant-numeric:tabular-nums;">${formatAHT(h.aht)}</td><td style="padding:10px;border:1px solid var(--card-border);">${h.activity_count}</td></tr>`;
        }
        html+='</tbody></table></div>';
        document.getElementById('historyContent').innerHTML=html;
    }catch(e){document.getElementById('historyContent').innerHTML=`<p style="text-align:center;color:var(--danger);">Ошибка: ${e.message}</p>`;}
}

/** Сравнение периодов */
async function loadComparison(){
    const empSelect=document.getElementById('compareEmployeeSelect');
    const p1Select=document.getElementById('comparePeriod1');
    const p2Select=document.getElementById('comparePeriod2');
    const empName=empSelect.value,period1=p1Select.value,period2=p2Select.value;
    if(!empName||!period1||!period2){document.getElementById('compareContent').innerHTML='<p style="text-align:center;color:var(--warning);">Заполните все поля</p>';return;}
    if(period1===period2){document.getElementById('compareContent').innerHTML='<p style="text-align:center;color:var(--warning);">Выберите разные периоды</p>';return;}
    document.getElementById('compareContent').innerHTML='<p style="text-align:center;">Сравнение...</p>';
    try{
        const url=`/api/compare/${encodeURIComponent(empName)}?period1=${encodeURIComponent(period1)}&period2=${encodeURIComponent(period2)}`;
        const res=await fetch(url);
        const data=await res.json();
        if(data.error){document.getElementById('compareContent').innerHTML=`<p style="text-align:center;color:var(--danger);">${data.error}</p>`;return;}
        const criteriaNames={greeting:'Приветствие',ethics:'Этика',crm:'CRM',legend:'Легендирование',informing:'Информирование',argumentation:'Аргументация',manipulation:'Манипуляция',requirements:'Требования',summary:'Итоги'};
        let html=`<h4 style="margin-bottom:15px;">⚖️ Сравнение: ${empName}</h4><div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;margin-bottom:20px;"><div style="background:rgba(255,255,255,0.05);padding:15px;border-radius:10px;"><div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:5px;">${data.period1}</div><div style="font-size:1.5rem;font-weight:700;">TQS: ${(data.tqs.period1*100).toFixed(1)}%</div><div style="font-size:1rem;">AHT: ${data.aht.period1?formatAHT(data.aht.period1):'—'}</div></div><div style="background:rgba(255,255,255,0.05);padding:15px;border-radius:10px;"><div style="font-size:0.85rem;color:var(--text-muted);margin-bottom:5px;">${data.period2}</div><div style="font-size:1.5rem;font-weight:700;">TQS: ${(data.tqs.period2*100).toFixed(1)}%</div><div style="font-size:1rem;">AHT: ${data.aht.period2?formatAHT(data.aht.period2):'—'}</div></div></div><div style="margin-bottom:20px;"><h5>Изменения:</h5><p><strong>TQS:</strong> <span style="color:${data.tqs.delta_pct>0?'var(--success)':'var(--danger)'};">${data.tqs.delta_pct>0?'+':''}${data.tqs.delta_pct}%</span> — ${data.tqs.interpretation}</p>${data.aht.interpretation?`<p><strong>AHT:</strong> <span style="color:${data.aht.delta_min<0?'var(--success)':'var(--danger)'};">${data.aht.delta_min>0?'+':''}${formatAHT(Math.abs(data.aht.delta_min))}</span> — ${data.aht.interpretation}</p>`:''}<p><strong>Звонков:</strong> ${data.activity.delta>0?'+':''}${data.activity.delta}</p></div><h5>По критериям:</h5><div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.85rem;"><thead><tr style="background:rgba(0,0,0,0.2);"><th style="padding:8px;border:1px solid var(--card-border);">Критерий</th><th style="padding:8px;border:1px solid var(--card-border);">${data.period1}</th><th style="padding:8px;border:1px solid var(--card-border);">${data.period2}</th><th style="padding:8px;border:1px solid var(--card-border);">Δ%</th><th style="padding:8px;border:1px solid var(--card-border);">Тренд</th></tr></thead><tbody>`;
        for(const[key,val]of Object.entries(data.scores_delta)){
            const c=val.delta_pct>0?'var(--success)':(val.delta_pct<0?'var(--danger)':'var(--text-muted)');
            const icon=val.trend==='up'?'📈':(val.trend==='down'?'📉':'➡️');
            html+=`<tr><td style="padding:8px;border:1px solid var(--card-border);">${criteriaNames[key]||key}</td><td style="padding:8px;border:1px solid var(--card-border);">${val.period1}%</td><td style="padding:8px;border:1px solid var(--card-border);">${val.period2}%</td><td style="padding:8px;border:1px solid var(--card-border);color:${c};font-weight:700;">${val.delta_pct>0?'+':''}${val.delta_pct}%</td><td style="padding:8px;border:1px solid var(--card-border);">${icon}</td></tr>`;
        }
        html+='</tbody></table></div>';
        document.getElementById('compareContent').innerHTML=html;
    }catch(e){document.getElementById('compareContent').innerHTML=`<p style="text-align:center;color:var(--danger);">Ошибка: ${e.message}</p>`;}
}

/** Заполнение периодов для сравнения (динамически по сотруднику) */
async function populateComparisonPeriods(){
    const empSelect=document.getElementById('compareEmployeeSelect');
    const p1Sel=document.getElementById('comparePeriod1');
    const p2Sel=document.getElementById('comparePeriod2');
    
    // Загружаем сотрудников если пусто
    if(empSelect.options.length<=1){
        try{
            const res=await fetch('/api/employees');
            const employees=await res.json();
            empSelect.innerHTML='<option value="">— Выберите —</option>';
            employees.sort((a,b)=>a.employee_name.localeCompare(b.employee_name)).forEach(emp=>{
                const o=document.createElement('option');o.value=emp.employee_name;o.textContent=emp.employee_name;empSelect.appendChild(o);
            });
        }catch(e){}
    }
    
    empSelect.onchange=async function(){
        const empName=this.value;
        if(!empName){p1Sel.innerHTML='<option value="">— Сначала выберите сотрудника —</option>';p2Sel.innerHTML='<option value="">—</option>';return;}
        p1Sel.innerHTML='<option value="">Загрузка...</option>';p2Sel.innerHTML='<option value="">Загрузка...</option>';
        try{
            const res=await fetch(`/api/history/${encodeURIComponent(empName)}?mode=detailed`);
            const data=await res.json();
            if(data.error){p1Sel.innerHTML='<option value="">Нет данных</option>';p2Sel.innerHTML='<option value="">—</option>';return;}
            // Уникальные периоды, отсортированные
            const periods=[...new Set(data.history.map(h=>h.period))];
            const sorted=sortPeriodsDesc(periods);
            p1Sel.innerHTML='<option value="">— Выберите —</option>';
            p2Sel.innerHTML='<option value="">— Выберите —</option>';
            sorted.forEach(p=>{
                const o1=document.createElement('option');o1.value=p;o1.textContent=p;p1Sel.appendChild(o1);
                const o2=document.createElement('option');o2.value=p;o2.textContent=p;p2Sel.appendChild(o2);
            });
            if(sorted.length>0)p1Sel.value=sorted[0];
            if(sorted.length>1)p2Sel.value=sorted[1];
        }catch(e){p1Sel.innerHTML='<option value="">Ошибка</option>';p2Sel.innerHTML='<option value="">—</option>';}
    };
}

/** Тренды с прогнозом Хольта + Chart.js */
async function loadTrendsForecast(){
    const select=document.getElementById('trendEmployeeSelect');
    let empName=select.value;
    if(!empName)empName='team';
    document.getElementById('trendsContent').innerHTML='<p style="text-align:center;">Загрузка прогноза...</p>';
    try{
        const url=empName==='team'?'/api/trends/forecast':`/api/trends/forecast?employee_name=${encodeURIComponent(empName)}`;
        const res=await fetch(url);
        const data=await res.json();
        if(data.error){document.getElementById('trendsContent').innerHTML=`<p style="text-align:center;color:var(--warning);">${data.error}</p>`;return;}
        
        const chartId=`trendChart_${Date.now()}`;
        const r2=data.tqs_forecast.r_squared;
        const r2Label=data.tqs_forecast.r_squared_label;
        const r2Color=r2>=0.7?'var(--success)':(r2>=0.5?'var(--warning)':'var(--danger)');
        const changeColor=data.change_pct>0?'var(--success)':'var(--danger)';
        const changeIcon=data.change_pct>0?'↗️':(data.change_pct<0?'↘️':'➡️');
        
        let html=`<h4 style="margin-bottom:10px;font-size:1rem;">📈 Прогноз TQS: ${data.employee_name==='team'?'Вся команда':data.employee_name}</h4>
            <div style="margin-bottom:15px;"><canvas id="${chartId}" style="width:100%;max-height:280px;background:rgba(0,0,0,0.06);border-radius:12px;padding:10px;"></canvas></div>
            
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:15px;">
                <div style="background:rgba(255,255,255,0.05);padding:14px;border-radius:10px;border:1px solid var(--card-border);">
                    <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;">📊 Точность модели (R²)</div>
                    <div style="font-size:1.4rem;font-weight:800;color:${r2Color};">${r2}</div>
                    <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">${r2Label}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);margin-top:8px;line-height:1.4;">
                        R² показывает насколько хорошо модель описывает данные. 
                        1.0 = идеальное соответствие, 0 = модель бесполезна.
                    </div>
                </div>
                <div style="background:rgba(255,255,255,0.05);padding:14px;border-radius:10px;border:1px solid var(--card-border);">
                    <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;">📈 Прогноз изменения</div>
                    <div style="font-size:1.4rem;font-weight:800;color:${changeColor};">${changeIcon} ${data.change_pct>0?'+':''}${data.change_pct}%</div>
                    <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">${data.business_outlook}</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);margin-top:8px;line-height:1.4;">
                        Текущий TQS: ${(data.current_tqs*100).toFixed(1)}% → Прогноз: ${(data.forecast_avg_tqs*100).toFixed(1)}%
                    </div>
                </div>
                <div style="background:rgba(255,255,255,0.05);padding:14px;border-radius:10px;border:1px solid var(--card-border);">
                    <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:6px;">🔧 Метод прогнозирования</div>
                    <div style="font-size:1rem;font-weight:700;">Holt's Smoothing</div>
                    <div style="font-size:0.75rem;color:var(--text-muted);margin-top:4px;">α=0.5 (уровень), β=0.3 (тренд)</div>
                    <div style="font-size:0.65rem;color:var(--text-muted);margin-top:8px;line-height:1.4;">
                        Экспоненциальное сглаживание с учётом тренда. Лучше линейной регрессии для нестабильных данных.
                    </div>
                </div>
            </div>`;
        
        // Рекомендации
        if(data.recommendations&&data.recommendations.length>0){
            html+=`<div style="background:rgba(249,115,22,0.08);padding:14px;border-radius:10px;border:1px solid rgba(249,115,22,0.2);margin-bottom:15px;">
                <h5 style="color:var(--accent-orange);margin-bottom:8px;">💡 Рекомендации на основе прогноза:</h5>
                <ul style="margin:0;padding-left:20px;">
                    ${data.recommendations.map(r=>`<li style="margin-bottom:4px;font-size:0.85rem;">${r}</li>`).join('')}
                </ul>
            </div>`;
        }
        
        // Прогнозные значения
        html+=`<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:15px;">
            <div style="background:rgba(96,165,250,0.1);padding:12px;border-radius:8px;text-align:center;border:1px solid rgba(96,165,250,0.2);">
                <div style="font-size:0.7rem;color:var(--text-muted);">Период +1</div>
                <div style="font-size:1.3rem;font-weight:700;color:var(--accent-orange);">${(data.tqs_forecast.values[0]*100).toFixed(1)}%</div>
            </div>
            <div style="background:rgba(96,165,250,0.1);padding:12px;border-radius:8px;text-align:center;border:1px solid rgba(96,165,250,0.2);">
                <div style="font-size:0.7rem;color:var(--text-muted);">Период +2</div>
                <div style="font-size:1.3rem;font-weight:700;color:var(--accent-orange);">${(data.tqs_forecast.values[1]*100).toFixed(1)}%</div>
            </div>
            <div style="background:rgba(96,165,250,0.1);padding:12px;border-radius:8px;text-align:center;border:1px solid rgba(96,165,250,0.2);">
                <div style="font-size:0.7rem;color:var(--text-muted);">Период +3</div>
                <div style="font-size:1.3rem;font-weight:700;color:var(--accent-orange);">${(data.tqs_forecast.values[2]*100).toFixed(1)}%</div>
            </div>
        </div>`;
        
        // Лучшие и худшие (без дубликатов)
        try{
            const bwRes=await fetch('/api/leaderboard/best-worst?limit=3');
            const bwData=await bwRes.json();
            if(bwData.best&&bwData.worst){
                // Удаляем дубликаты по имени
                const uniqueNames=new Set();
                const filterUnique=(list)=>list.filter(e=>{if(uniqueNames.has(e.employee_name))return false;uniqueNames.add(e.employee_name);return true;});
                const bestUnique=filterUnique([...bwData.best]);
                uniqueNames.clear();
                const worstUnique=filterUnique([...bwData.worst]);
                
                html+=`<div style="display:grid;grid-template-columns:1fr 1fr;gap:15px;">
                    <div style="background:rgba(74,222,128,0.08);padding:12px;border-radius:10px;border:1px solid rgba(74,222,128,0.2);">
                        <h5 style="color:var(--success);margin-bottom:8px;">🏆 Лучшие по TQS</h5>
                        ${bestUnique.map((e,i)=>`<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:0.85rem;border-bottom:1px solid rgba(255,255,255,0.05);"><span>${i+1}. ${e.employee_name}</span><strong style="color:var(--success);">${(e.tqs*100).toFixed(0)}%</strong></div>`).join('')}
                    </div>
                    <div style="background:rgba(248,113,113,0.08);padding:12px;border-radius:10px;border:1px solid rgba(248,113,113,0.2);">
                        <h5 style="color:var(--danger);margin-bottom:8px;">⚠️ Отстающие по TQS</h5>
                        ${worstUnique.map((e,i)=>`<div style="display:flex;justify-content:space-between;padding:5px 0;font-size:0.85rem;border-bottom:1px solid rgba(255,255,255,0.05);"><span>${i+1}. ${e.employee_name}</span><strong style="color:var(--danger);">${(e.tqs*100).toFixed(0)}%</strong></div>`).join('')}
                    </div>
                </div>`;
            }
        }catch(e){}
        
        document.getElementById('trendsContent').innerHTML=html;
        setTimeout(()=>drawChartJS(chartId,data),100);
    }catch(e){document.getElementById('trendsContent').innerHTML=`<p style="text-align:center;color:var(--danger);">Ошибка: ${e.message}</p>`;}
}

/** Chart.js график — контрастный для обеих тем */
function drawChartJS(canvasId,data){
    const ctx=document.getElementById(canvasId);
    if(!ctx||!window.Chart)return;
    
    const hist=data.historical;
    const forecast=data.tqs_forecast.values;
    const r2=data.tqs_forecast.r_squared;
    
    const labels=hist.map(h=>h.period).concat(forecast.map((_,i)=>`Прогноз +${i+1}`));
    
    const actualData=hist.map(h=>h.tqs*100).concat(new Array(forecast.length).fill(null));
    const fittedData=hist.map(h=>(h.tqs_fitted||h.tqs)*100).concat(new Array(forecast.length).fill(null));
    const forecastData=[...new Array(hist.length-1).fill(null),hist[hist.length-1].tqs*100,...forecast.map(v=>v*100)];
    
    // Определяем тему
    const isLight=document.body.getAttribute('data-theme')==='light';
    const textColor=isLight?'#1e293b':'#f1f5f9';
    const gridColor=isLight?'rgba(0,0,0,0.1)':'rgba(255,255,255,0.08)';
    const tooltipBg=isLight?'rgba(255,255,255,0.97)':'rgba(15,23,42,0.97)';
    const tooltipBorder=isLight?'rgba(0,0,0,0.15)':'rgba(255,255,255,0.15)';
    const tooltipText=isLight?'#0f172a':'#f8fafc';
    
    new Chart(ctx,{
        type:'line',
        data:{
            labels,
            datasets:[
                {
                    label:'Факт TQS',
                    data:actualData,
                    borderColor:'#10b981',
                    backgroundColor:'rgba(16,185,129,0.08)',
                    borderWidth:3,
                    pointRadius:5,
                    pointBackgroundColor:'#10b981',
                    pointBorderColor:isLight?'#fff':'#1e293b',
                    pointBorderWidth:2,
                    pointHoverRadius:7,
                    tension:0.3,
                    fill:false
                },
                {
                    label:'Модель',
                    data:fittedData,
                    borderColor:'rgba(16,185,129,0.5)',
                    borderWidth:2,
                    borderDash:[6,4],
                    pointRadius:0,
                    tension:0.3,
                    fill:false
                },
                {
                    label:'Прогноз',
                    data:forecastData,
                    borderColor:'#3b82f6',
                    backgroundColor:'rgba(59,130,246,0.08)',
                    borderWidth:3,
                    borderDash:[10,5],
                    pointRadius:6,
                    pointBackgroundColor:'#3b82f6',
                    pointBorderColor:isLight?'#fff':'#1e293b',
                    pointBorderWidth:2,
                    pointHoverRadius:8,
                    tension:0.3,
                    fill:false
                }
            ]
        },
        options:{
            responsive:true,
            maintainAspectRatio:false,
            interaction:{mode:'index',intersect:false},
            plugins:{
                legend:{
                    labels:{
                        color:textColor,
                        font:{size:12,weight:'600'},
                        usePointStyle:true,
                        pointStyle:'circle',
                        padding:20,
                        generateLabels:chart=>{
                            const datasets=chart.data.datasets;
                            return datasets.map((ds,i)=>({
                                text:ds.label,
                                fillStyle:ds.borderColor,
                                strokeStyle:ds.borderColor,
                                lineWidth:ds.borderWidth,
                                hidden:!chart.isDatasetVisible(i),
                                index:i
                            }));
                        }
                    }
                },
                tooltip:{
                    backgroundColor:tooltipBg,
                    titleColor:tooltipText,
                    bodyColor:tooltipText,
                    titleFont:{size:13,weight:'700'},
                    bodyFont:{size:12},
                    borderColor:tooltipBorder,
                    borderWidth:1,
                    padding:14,
                    cornerRadius:10,
                    boxPadding:6,
                    usePointStyle:true,
                    callbacks:{
                        label:ctx=>{
                            const val=ctx.parsed.y;
                            return val!==null?`${ctx.dataset.label}: ${val.toFixed(1)}%`:null;
                        },
                        afterBody:items=>{
                            const idx=items[0]?.dataIndex;
                            if(idx>=hist.length){
                                const fIdx=idx-hist.length;
                                return [`Прогноз (Holt α=0.5 β=0.3)`];
                            }
                            return[`R² = ${r2}`];
                        }
                    }
                }
            },
            scales:{
                x:{
                    ticks:{
                        color:textColor,
                        font:{size:10,weight:'500'},
                        maxRotation:45,
                        autoSkip:true,
                        maxTicksLimit:12
                    },
                    grid:{
                        color:gridColor,
                        lineWidth:1
                    }
                },
                y:{
                    ticks:{
                        color:textColor,
                        font:{size:11,weight:'600'},
                        callback:v=>v+'%',
                        stepSize:5
                    },
                    grid:{
                        color:gridColor,
                        lineWidth:1
                    },
                    suggestedMin:Math.min(...actualData.filter(v=>v!==null))*0.92,
                    suggestedMax:Math.max(...[...actualData.filter(v=>v!==null),...forecastData.filter(v=>v!==null)])*1.05
                }
            }
        }
    });
}

/** Инициализация */
document.addEventListener('DOMContentLoaded',()=>{
    setTimeout(()=>{
        if(!window.DASHBOARD_DATA)return;
        const employees=Object.keys(window.DASHBOARD_DATA).filter(k=>k!=='_meta_pdf_summary');
        const histSel=document.getElementById('historyEmployeeSelect');
        if(histSel){histSel.innerHTML='<option value="">— Выберите —</option>';employees.sort().forEach(emp=>{const o=document.createElement('option');o.value=emp;o.textContent=emp;histSel.appendChild(o);});}
        const trendSel=document.getElementById('trendEmployeeSelect');
        if(trendSel){trendSel.innerHTML='<option value="team">📊 Вся команда</option>';employees.sort().forEach(emp=>{const o=document.createElement('option');o.value=emp;o.textContent=emp;trendSel.appendChild(o);});}
    },300);
});
