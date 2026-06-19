class PorcentajePanaderoFormulaCard extends HTMLElement {
  constructor() { 
    super(); 
    this.attachShadow({ mode: 'open' }); 
    this._htmlInyectado = false; 
  }
  
  set hass(hass) { 
    this._hass = hass; 
    if (!this.content) this.initCard(); 
    this.updateCard(); 
  }
  
  setConfig(config) { 
    this.config = config; 
  }

  initCard() {
    const style = document.createElement('style');
    style.textContent = `
      ha-card { padding: 16px; font-family: var(--paper-font-body1_-_font-family, inherit); box-sizing: border-box; }
      .control-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 16px; width: 100%; box-sizing: border-box; }
      .select-formula-receta { flex: 1; padding: 10px; border-radius: 8px; border: 1px solid var(--divider-color, #ccc); background-color: var(--card-background-color, #fff); color: var(--primary-text-color); font-size: 14px; font-weight: bold; width: 60%; }
      .btn-reset-receta { background-color: var(--error-color, #db4437); color: white; border: none; padding: 10px 14px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 13px; white-space: nowrap; }
      .obrador-title { font-size: 18px; font-weight: bold; margin-bottom: 12px; display: flex; color: var(--primary-text-color); width: 100%; align-items: center; }
      .panel-section { border-left: 3px solid var(--accent-color); padding-left: 10px; margin: 16px 0 8px 0; font-weight: bold; text-transform: uppercase; font-size: 14px; color: var(--accent-color); }
      .ingrediente-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); font-size: 14px !important; font-family: inherit !important; }
      .ingrediente-nombre { font-weight: 500 !important; font-size: 14px !important; } 
      .ingrediente-gramos { font-weight: bold !important; font-size: 16px !important; }
    `;
    const card = document.createElement('ha-card'); 
    this.content = document.createElement('div');
    card.appendChild(this.content); 
    this.shadowRoot.appendChild(style); 
    this.shadowRoot.appendChild(card);
  }

  updateCard() {
    if (!this._hass) return; 
    const lang = this._hass.language || 'es', isEn = lang.startsWith('en');
    const selectReceta = this._hass.states['select.formula_de_receta'], recetaSeleccionada = selectReceta?.state || '---', opcionesRecetas = selectReceta?.attributes['options'] || [];
    let recetaActiva = this._hass.states['sensor.receta_en_el_obrador']?.state || '', recetaLimpia = recetaActiva.trim().toLowerCase();
    
    if (!recetaActiva || recetaLimpia === '---' || recetaLimpia === 'unknown' || recetaLimpia === 'none' || recetaLimpia === '') { 
      recetaActiva = isEn ? 'EMPIRICAL METHOD !' : 'MÉTODO EMPÍRICO !'; 
    }
    
    const h1 = parseFloat(this._hass.states['sensor.pan_harina_1_neta']?.state || 0), h2 = parseFloat(this._hass.states['sensor.pan_harina_2_neta']?.state || 0), h3 = parseFloat(this._hass.states['sensor.pan_harina_3_neta']?.state || 0);
    const agua = parseFloat(this._hass.states['sensor.pan_agua_neta']?.state || 0), sal = parseFloat(this._hass.states['sensor.pan_sal_neta']?.state || 0), leva = parseFloat(this._hass.states['sensor.pan_levadura_neta']?.state || 0);
    const marcaH1 = this._hass.states['select.harina_principal_1']?.state || (isEn ? 'FLOUR 1' : 'HARINA 1');
    const tzTotal = parseFloat(this._hass.states['sensor.tang_zhong_total']?.state || 0), pctPref = parseFloat(this._hass.states['number.prefermento']?.state || 0);

    if (!this._htmlInyectado) {
      const titleYaml = this.config && this.config.title ? `<div style="font-size: 24px; font-weight: normal; color: var(--primary-text-color); margin-bottom: 16px; padding: 4px 0 12px 0;">${this.config.title}</div>` : '';
      
      this.content.innerHTML = `
        ${titleYaml}
        <div class="control-header">
          <select class="select-formula-receta" id="select-formula-card"></select>
          <button class="btn-reset-receta" id="btn-reset-card">🔄 ${isEn ? 'RESET' : 'RESTABLECER'}</button>
        </div>
        <div class="obrador-title">
          <span id="cabecera-receta-dinamica" style="font-size:14px !important; font-weight:normal; margin-left:auto; color:var(--secondary-text-color); text-transform: uppercase; letter-spacing: 0.5px;"></span>
        </div>
        <div id="bloque-tangzhong-dinamico"></div>
        <div id="bloque-prefermento-dinamico"></div>
        <div class="panel-section">${isEn ? 'FINAL KNEADING INGREDIENTS' : 'INGREDIENTES AMASADO FINAL'}</div>
        <div id="lista-ingredientes"></div>
      `;
      this.registrarEventosCard(); 
      this._htmlInyectado = true;
    }

    const activeEl = this.shadowRoot.activeElement, selF = this.shadowRoot.getElementById('select-formula-card');
    
    if (selF && selF !== activeEl) { 
      selF.innerHTML = opcionesRecetas.map(opt => `<option value="${opt}" ${opt === recetaSeleccionada ? 'selected' : ''}>${opt.toUpperCase()}</option>`).join(''); 
    }
    
    const cabeceraTexto = this.shadowRoot.getElementById('cabecera-receta-dinamica'); 
    if (cabeceraTexto) cabeceraTexto.textContent = recetaActiva;
    
    const cf = (n, g) => `<div class="ingrediente-row"><span class="ingrediente-nombre">${n}</span><span class="ingrediente-gramos">${g ? `${g} g` : ''}</span></div>`;

    const divTZ = this.shadowRoot.getElementById('bloque-tangzhong-dinamico');
    if (divTZ) {
      let hTZ = ''; 
      if (tzTotal > 0) {
        const tzHarina = parseFloat(this._hass.states['sensor.tang_zhong_total']?.attributes['harina_g'] || 0), tzLiquido = parseFloat(this._hass.states['sensor.tang_zhong_total']?.attributes['liquido_total_g'] || 0);
        const tzLeche = parseFloat(this._hass.states['sensor.tang_zhong_total']?.attributes['leche_utilizada_g'] || 0), tzAguaAsis = parseFloat(this._hass.states['sensor.tang_zhong_total']?.attributes['agua_asistencia_g'] || 0);
        const tzBase = this._hass.states['sensor.tang_zhong_total']?.attributes['base_solicitada'] || 'agua', pctTZ = parseFloat(this._hass.states['number.tang_zhong']?.state || 0), esM = (tzBase === 'leche' && tzLeche > 0 && tzAguaAsis > 0);
        hTZ += `<div class="panel-section" style="border-left-color:#ff9800;color:#ff9800;">${isEn ? 'TANG-ZHONG PREPARATION' : 'PREPARACION TANG-ZHONG'}</div>${cf('• ' + (isEn ? 'FLOUR TO SCALD' : 'HARINA A ESCALDAR') + ` (${pctTZ}%)`, tzHarina)}<div class="ingrediente-row"><span class="ingrediente-nombre">• ${isEn ? 'REQUIRED LIQUID (1:5)' : 'LIQUIDO REQUERIDO (1:5)'} [${tzBase.toUpperCase()}] ${esM ? '' : `(${pctTZ * 5}%)`}</span><span class="ingrediente-gramos">${esM ? '' : `${tzLiquido} g`}</span></div>`;
        if (esM) {
          const pL = tzLiquido > 0 ? Math.round((tzLeche / tzLiquido) * 100) : 0, pW = tzLiquido > 0 ? Math.round((tzAguaAsis / tzLiquido) * 100) : 0;
          hTZ += `<div class="ingrediente-row"><span class="ingrediente-nombre" style="padding-left:12px;color:var(--secondary-text-color);font-weight:500;">- ${isEn ? `MILK (${pL}%) (AVAILABLE)` : `LECHE (${pL}%) (DISPONIBLE)`}</span><span class="ingrediente-gramos" style="color:var(--primary-text-color);">${tzLeche} g</span></div><div class="ingrediente-row"><span class="ingrediente-nombre" style="padding-left:12px;color:var(--secondary-text-color);font-weight:500;">- ${isEn ? `WATER (${pW}%)` : `AGUA (${pW}%)`}</span><span class="ingrediente-gramos" style="color:var(--primary-text-color);">${tzAguaAsis} g</span></div><div style="background-color:rgba(255,152,0,0.1);padding:10px;border-radius:8px;color:#ff9800;margin-top:8px;border:1px solid rgba(255,152,0,0.2);"><div style="font-size:13px;font-weight:900;letter-spacing:1px;margin-bottom:4px;text-align:left;">⚠️ ${isEn ? 'ALERT' : 'ALERTA'}</div><div style="font-size:11px;font-weight:bold;opacity:0.9;line-height:1.3;text-align:center;">${isEn ? 'MIXED SCALDING: NOT ENOUGH MILK, WATER ADDED!' : 'ESCALDADO MIXTO: LECHE INSUFICIENTE, SE APORTA AGUA!'}</div></div>`;
        }
      } 
      divTZ.innerHTML = hTZ;
    }

    const divP = this.shadowRoot.getElementById('bloque-prefermento-dinamico');
    if (divP) {
      let hP = ''; if (pctPref > 0) {
        const tPref = (this._hass.states['select.tipo_de_prefermento']?.state || 'poolish').toLowerCase(), hPref = parseFloat(this._hass.states['sensor.pan_harina_prefermento']?.state || 0);
        const aPref = parseFloat(this._hass.states['sensor.pan_agua_prefermento']?.state || 0), lPref = parseFloat(this._hass.states['sensor.pan_levadura_prefermento']?.state || 0), inoculo = parseFloat(this._hass.states['sensor.pan_inoculo_masa_madre']?.state || 0);
        let nomS = isEn ? 'PREFERMENT PREPARATION' : 'PREPARACION DEL PREFERMENTO'; if (tPref === 'masa madre') nomS = isEn ? 'SOURDOUGH REFRESHMENT' : 'REFRESCO DE MASA MADRE'; else if (tPref === 'biga') nomS = isEn ? 'BIGA PREPARATION' : 'PREPARACION DE BIGA'; else if (tPref === 'poolish') nomS = isEn ? 'POOLISH PREPARATION' : 'PREPARACION DE POOLISH';
        hP += `<div class="panel-section" style="border-left-color: var(--primary-color); color: var(--primary-color);">${nomS}</div>`;
        if (tPref === 'masa madre') { const pctI = this._hass.states['sensor.porcentaje_inoculo_receta']?.state || '33.3'; hP += `<div class="ingrediente-row"><span style="font-weight: 500;">${isEn ? 'SOURDOUGH INOCULUM' : 'INOCULO MASA MADRE'} (${pctI}%)</span><span class="ingrediente-gramos">${inoculo} g</span></div>`; }
        else { 
          const tL = (this._hass.states['button.alternar_fresca_seca']?.state || 'fresca').toUpperCase(), pL = this._hass.states['number.levadura_prefermento']?.state || '0'; 
          const textoLevaPref = isEn ? `${tL} YEAST` : `LEVADURA ${tL}`;
          hP += `<div class="ingrediente-row"><span style="font-weight: 500;">${textoLevaPref} (${pL}%)</span><span class="ingrediente-gramos">${lPref} g</span></div>`; 
        }
        const pctHP = this._hass.states['sensor.harina_prefermentada']?.state || '0', pctAP = this._hass.states['sensor.hidratacion_del_prefermento']?.state || '100';
        hP += `<div class="ingrediente-row"><span style="font-weight: 500;">${marcaH1.toUpperCase()} (${pctHP}%)</span><span class="ingrediente-gramos">${hPref} g</span></div><div class="ingrediente-row"><span style="font-weight: 500;">${isEn?'WATER':'AGUA'} (${pctAP}%)</span><span class="ingrediente-gramos">${aPref} g</span></div>`;
      } divP.innerHTML = hP;
    }

    const lista = this.shadowRoot.getElementById('lista-ingredientes');
    if (lista) {
      let hI = ''; const pH1 = this._hass.states['sensor.porcentaje_neto_harina_1']?.state || '0', pH2 = this._hass.states['sensor.porcentaje_neto_harina_2']?.state || '0', pH3 = this._hass.states['sensor.porcentaje_neto_harina_3']?.state || '0';
      const pA = this._hass.states['sensor.porcentaje_hidratacion_final']?.state || '0', pS = this._hass.states['number.sal']?.state || '2', pL = this._hass.states['number.levadura']?.state || '0';
      const marcaH2 = this._hass.states['select.harina_secundaria_2']?.state || (isEn ? 'FLOUR 2' : 'HARINA 2'), marcaH3 = this._hass.states['select.harina_secundaria_3']?.state || (isEn ? 'FLOUR 3' : 'HARINA 3');
      
      const tLevaFinal = (this._hass.states['button.alternar_fresca_seca']?.state || 'fresca').toUpperCase();
      const textoLevaFinal = isEn ? `${tLevaFinal} YEAST` : `LEVADURA ${tLevaFinal}`;

      if (h1 > 0) hI += cf(`${marcaH1.toUpperCase()} (${pH1}%)`, h1); if (h2 > 0) hI += cf(`${marcaH2.toUpperCase()} (${pH2}%)`, h2); if (h3 > 0) hI += cf(`${marcaH3.toUpperCase()} (${pH3}%)`, h3);
      if (agua > 0) hI += cf(`${isEn ? 'WATER' : 'AGUA'} (${pA}%)`, agua); if (sal > 0) hI += cf(`${isEn ? 'SALT' : 'SAL'} (${pS}%)`, sal); 
      
      if (leva > 0 || parseFloat(pL) > 0) hI += cf(`${textoLevaFinal} (${pL}%)`, leva);
      
      if (pctPref > 0) { const tPrefReal = (this._hass.states['select.tipo_de_prefermento']?.state || 'POOLISH').toUpperCase(), totPrefPct = this._hass.states['sensor.pan_prefermento_total']?.state || '0', grPrefReales = this._hass.states['sensor.pan_prefermento_total']?.attributes['gramos_totales_reales'] || 0; if (grPrefReales > 0) hI += cf(`${tPrefReal} (${totPrefPct}%)`, grPrefReales); }
      if (tzTotal > 0) { const pctTZMando = this._hass.states['number.tang_zhong']?.state || '0'; hI += cf(`TANG-ZHONG (${pctTZMando}%)`, tzTotal); }
      const malta = parseFloat(this._hass.states['sensor.pan_malta']?.state || 0), azucar = parseFloat(this._hass.states['sensor.pan_azucar']?.state || 0), mantequilla = parseFloat(this._hass.states['sensor.pan_mantequilla']?.state || 0);
      const aove = parseFloat(this._hass.states['sensor.pan_aove']?.state || 0), leche = parseFloat(this._hass.states['sensor.pan_leche']?.state || 0), lechePolvo = parseFloat(this._hass.states['sensor.pan_leche_polvo']?.state || 0), huevo = parseFloat(this._hass.states['sensor.pan_huevo']?.state || 0);
      const pM = this._hass.states['number.malta']?.state || '0', pAz = this._hass.states['number.azucar']?.state || '0', pMant = this._hass.states['number.mantequilla']?.state || '0', pAo = this._hass.states['number.aove']?.state || '0', pLec = this._hass.states['number.leche_liquida']?.state || '0', pLecP = this._hass.states['number.leche_en_polvo']?.state || '0', pHu = this._hass.states['number.huevo']?.state || '0';
      if (malta > 0) hI += cf(`${isEn ? 'MALT' : 'MALTA'} (${pM}%)`, malta); if (azucar > 0) hI += cf(`${isEn ? 'SUGAR' : 'AZUCAR'} (${pAz}%)`, azucar); if (mantequilla > 0) hI += cf(`${isEn ? 'BUTTER' : 'MANTEQUILLA'} (${pMant}%)`, mantequilla);
      if (aove > 0) { let exA = isEn ? 'EVOO' : 'AOVE'; if (this._hass.states['sensor.receta_en_el_obrador']?.state?.toLowerCase().includes('detroit')) exA += isEn ? ' (grease pan)' : ' (engrasar molde)'; hI += cf(`${exA} (${pAo}%)`, aove); }
      if (leche > 0) hI += cf(`${isEn ? 'MILK' : 'LECHE'} (${pLec}%)`, leche); if (lechePolvo > 0) hI += cf(`${isEn ? 'MILK POWDER 26%' : 'LECHE EN POLVO 26%'} (${pLecP}%)`, lechePolvo); if (huevo > 0) hI += cf(`${isEn ? 'EGG' : 'HUEVO'} (${pHu}%)`, huevo);
      const pesoMasaTotal = parseFloat(this._hass.states['number.masa_final_objetivo']?.state || 1000).toFixed(0);
      hI += `<div class="panel-section" style="border-left-color:var(--accent-color);color:var(--accent-color);margin-top:20px;">${isEn?'TOTAL DOUGH WEIGHT':'PESO TOTAL DE LA MASA'}</div><div class="ingrediente-row" style="border-bottom:none;"><span class="ingrediente-nombre" style="font-weight:bold;color:var(--primary-text-color);">${isEn?'CONSOLIDATED TOTAL':'PESO NETO TOTAL'}</span><span class="ingrediente-gramos" style="color:var(--accent-color,#ff9800);font-size:17px;font-weight:bold;margin-left:auto;">${pesoMasaTotal} g</span></div>`;
      lista.innerHTML = hI;
    }
  }
  registrarEventosCard() {
    this.shadowRoot.getElementById('btn-reset-card').addEventListener('click', () => { this._hass.callService('button', 'press', { entity_id: 'button.restablecer_parametros_base' }); });
    this.shadowRoot.getElementById('select-formula-card').addEventListener('change', (e) => { this._hass.callService('select', 'select_option', { entity_id: 'select.formula_de_receta', option: e.target.value }); });
  }
  getCardSize() { return 6; }
}
customElements.define('porcentaje-panadero-formula-card', PorcentajePanaderoFormulaCard);





class PorcentajePanaderoInfoCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._htmlInyectado = false; }
  set hass(hass) { this._hass = hass; if (!this.content) this.initCard(); this.updateCard(); }
  setConfig(config) { this.config = config; }
  initCard() {
    const style = document.createElement('style');
    style.textContent = `
      ha-card { padding: 16px; font-family: var(--paper-font-body1_-_font-family, inherit); box-sizing: border-box; }
      .panel-section { border-left: 3px solid var(--accent-color); padding-left: 10px; margin: 18px 0 8px 0; font-weight: bold; text-transform: uppercase; font-size: 14px; color: var(--accent-color); }
      .ingrediente-row { display: flex; justify-content: space-between; align-items: center; padding: 8px 0; border-bottom: 1px solid var(--divider-color, #e0e0e0); font-size: 14px; }
      .ingrediente-nombre { font-weight: 500; } .ingrediente-gramos { font-weight: bold; font-size: 16px; }
      .badge-control { font-size: 11px; padding: 2px 6px; border-radius: 4px; font-weight: bold; background-color: var(--secondary-background-color); color: var(--secondary-text-color); margin-left: 6px; text-transform: uppercase; }
      .badge-activo { background-color: rgba(33, 150, 243, 0.15) !important; color: #2196f3 !important; border: 1px solid rgba(33, 150, 243, 0.3); }
    `;
    const card = document.createElement('ha-card'); this.content = document.createElement('div');
    card.appendChild(this.content); this.shadowRoot.appendChild(style); this.shadowRoot.appendChild(card);
  }
  updateCard() {
    if (!this._hass) return; const lang = this._hass.language || 'es'; const isEn = lang.startsWith('en');

    const tAguaIdeal = this._hass.states['sensor.pan_temperatura_agua_ideal']?.state || '---';
    const tFisica = this._hass.states['sensor.temperatura_real']?.state || '---';
    const origenTemp = (this._hass.states['select.origen_temperatura_levado']?.state || 'ambiente').toLowerCase();

    const tiempoLevado = this._hass.states['sensor.tiempo_de_levado_estimado']?.state || '---';
    const horaFin = this._hass.states['sensor.hora_de_masa_lista_aproximada']?.state || '---';

    const totHarinaG = this._hass.states['sensor.pan_harina_total']?.state || '0';
    const totHarinaPct = this._hass.states['sensor.porcentaje_harina_total']?.state || '100';
    const totAguaG = this._hass.states['sensor.pan_agua_total']?.state || '0';
    const totAguaPct = this._hass.states['number.agua_hidratacion']?.state || '0';
    
    const tzTotal = parseFloat(this._hass.states['sensor.tang_zhong_total']?.state || 0);
    const tzPct = parseFloat(this._hass.states['number.tang_zhong']?.state || 0);
    const pctPref = parseFloat(this._hass.states['number.prefermento']?.state || 0);
    const tipoPref = (this._hass.states['select.tipo_de_prefermento']?.state || 'poolish').toLowerCase();

    if (!this._htmlInyectado) {
      const titleYaml = this.config && this.config.title ? `<div style="font-size: 24px; font-weight: normal; color: var(--primary-text-color); margin-bottom: 16px; padding: 4px 0 12px 0;">${this.config.title}</div>` : '';

      this.content.innerHTML = `
        ${titleYaml}
        <div class="panel-section" style="border-left-color: #2196f3; color: #2196f3;">${isEn ? 'TEMPERATURE TELEMETRY' : 'CONTROL TÉRMICO Y SONDAS'}</div>
        <div class="ingrediente-row"><span class="ingrediente-nombre">${isEn ? 'IDEAL WATER TEMPERATURE' : 'TEMPERATURA IDEAL DEL AGUA'}</span><span class="ingrediente-gramos" style="color: #2196f3; font-size: 16px;"><span id="val-agua-ideal">---</span> °C</span></div>
        <div class="ingrediente-row"><span class="ingrediente-nombre" id="lbl-temp-ambient-dinamica">TEMPERATURA</span><span class="ingrediente-gramos"><span id="val-temp-fisica">---</span> °C</span></div>
        <div class="panel-section" style="border-left-color: #ff9800; color: #ff9800;">${isEn ? 'PROOFING MANAGEMENT' : 'CONTROL DE FERMENTACIÓN'}</div>
        <div class="ingrediente-row"><span class="ingrediente-nombre">${isEn ? 'ESTIMATED PROOFING TIME' : 'TIEMPO DE LEVADO ESTIMADO'}</span><span class="ingrediente-gramos" id="val-tiempo-levado">---</span></div>
        <div class="ingrediente-row"><span class="ingrediente-nombre">${isEn ? 'APPROX READY TIME' : 'HORA APROXIMADA DE MASA LISTA'}</span><span class="ingrediente-gramos" style="color: var(--success-color, #4caf50);" id="val-hora-fin">---</span></div>
        <div class="ingrediente-row"><span class="ingrediente-nombre" id="lbl-control-origen-dinamico">CONTROL DE TEMPERATURA</span><span class="ingrediente-gramos"></span></div>
        <div class="panel-section" style="border-left-color: var(--success-color, #4caf50); color: var(--success-color, #4caf50);">${isEn ? 'TOTALS SUMMARY' : 'RESUMEN DE TOTALES'}</div>
        <div class="ingrediente-row"><span class="ingrediente-nombre">${isEn ? 'TOTAL FLOUR' : 'TOTAL HARINA'} (<span id="pct-harina-tot">100</span>%)</span><span class="ingrediente-gramos" id="val-harina-tot">0 g</span></div>
        <div class="ingrediente-row"><span class="ingrediente-nombre">${isEn ? 'TOTAL WATER' : 'TOTAL AGUA'} (<span id="pct-agua-tot">0</span>%)</span><span class="ingrediente-gramos" id="val-agua-tot">0 g</span></div>
        <div id="bloque-info-tz-dinamico"></div><div id="bloque-info-pref-dinamico"></div>
      `;
      this._htmlInyectado = true;
    }

    const refEl = (id, txt) => { const el = this.shadowRoot.getElementById(id); if (el) el.textContent = txt; };
    refEl('val-agua-ideal', tAguaIdeal); refEl('val-temp-fisica', tFisica); refEl('val-tiempo-levado', tiempoLevado); refEl('val-hora-fin', horaFin);
    refEl('pct-harina-tot', totHarinaPct); refEl('val-harina-tot', `${totHarinaG} g`); refEl('pct-agua-tot', totAguaPct); refEl('val-agua-tot', `${totAguaG} g`);

    const lblTempAmbient = this.shadowRoot.getElementById('lbl-temp-ambient-dinamica');
    const lblControlOrigen = this.shadowRoot.getElementById('lbl-control-origen-dinamico');
    
    if (lblTempAmbient) {
      if (tFisica === '---' || tFisica === 'unknown' || tFisica === 'unavailable') {
        lblTempAmbient.innerHTML = `TEMPERATURA <span class="badge-control">MANUAL</span>`;
      } else {
        lblTempAmbient.innerHTML = `TEMPERATURA AMBIENTE <span class="badge-control badge-activo">SENSOR</span>`;
      }
    }
    
    if (lblControlOrigen) {
      const oL = origenTemp.trim().toLowerCase();
      if (oL.includes('sensor') || oL.includes('fisico') || oL.includes('sonda') || oL.includes('ambiente') || oL.includes('real')) {
        lblControlOrigen.innerHTML = `CONTROL DE TEMPERATURA <span class="badge-control badge-activo">SENSOR</span>`;
      } else {
        lblControlOrigen.innerHTML = `CONTROL DE TEMPERATURA <span class="badge-control">MANUAL</span>`;
      }
    }

    const divTZ = this.shadowRoot.getElementById('bloque-info-tz-dinamico');
    if (divTZ) { divTZ.innerHTML = tzTotal > 0 ? `<div class="ingrediente-row"><span class="ingrediente-nombre">TOTAL TANG-ZHONG (${tzPct}%)</span><span class="ingrediente-gramos">${tzTotal} g</span></div>` : ''; }

    const divPref = this.shadowRoot.getElementById('bloque-info-pref-dinamico');
    if (divPref) {
      if (pctPref > 0) {
        const totPrefPct = this._hass.states['sensor.pan_prefermento_total']?.state || '0';
        const grPrefReales = this._hass.states['sensor.pan_prefermento_total']?.attributes['gramos_totales_reales'] || 0;
        divPref.innerHTML = `<div class="ingrediente-row" style="border-bottom: none;"><span class="ingrediente-nombre">TOTAL ${tipoPref.toUpperCase()} (${totPrefPct}%)</span><span class="ingrediente-gramos">${grPrefReales} g</span></div>`;
      } else { divPref.innerHTML = ''; }
    }
  }
  getCardSize() { return 6; }
}
customElements.define('porcentaje-panadero-info-card', PorcentajePanaderoInfoCard);





class PorcentajePanaderoControlPanelCard extends HTMLElement {
  constructor() { super(); this.attachShadow({ mode: 'open' }); this._htmlInyectado = false; }
  set hass(hass) { this._hass = hass; if (!this.content) this.initCard(); this.updateCard(); }
  setConfig(config) { this.config = config; }
  initCard() {
    const style = document.createElement('style');
    style.textContent = `
      ha-card { padding: 18px; font-family: var(--paper-font-body1_-_font-family, inherit); border-radius: var(--ha-card-border-radius, 16px); }
      .sub-seccion { border-left: 4px solid var(--primary-color, #ff9800); padding-left: 12px; margin: 20px 0 12px 0; font-size: 13px; font-weight: bold; color: var(--primary-text-color); text-transform: uppercase; letter-spacing: 0.5px; }
      .divider { height: 1px; background-color: var(--divider-color, rgba(0,0,0,0.1)); margin: 16px 0; width: 100%; }
      .fila-inline { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; width: 100%; box-sizing: border-box; }
      .input-text-pan { flex: 1; padding: 11px; border-radius: 6px; border: 1px solid var(--divider-color, #ccc); background-color: var(--card-background-color, #fff); color: var(--primary-text-color); font-size: 14px; }
      .btn-guardar { background-color: var(--success-color, #4caf50); color: white; border: none; padding: 11px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px; white-space: nowrap; }
      .btn-eliminar { background-color: var(--error-color, #db4437); color: white; border: none; padding: 11px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; font-size: 13px; white-space: nowrap; }
      .btn-gestion-bloque { display: flex; gap: 10px; margin-bottom: 14px; }
      .btn-gestion-bloque button { flex: 1; height: 42px; border: none; border-radius: 6px; font-weight: bold; font-size: 13px; cursor: pointer; color: white; }
      select { width: 100%; padding: 11px; border-radius: 6px; border: 1px solid var(--divider-color, #ccc); background-color: var(--card-background-color, #fff); color: var(--primary-text-color); font-size: 14px; font-weight: bold; margin-bottom: 12px; box-sizing: border-box; }
    `;
    const card = document.createElement('ha-card'); this.content = document.createElement('div');
    card.appendChild(this.content); this.shadowRoot.appendChild(style); this.shadowRoot.appendChild(card);
  }
  updateCard() {
    if (!this._hass) return; const lang = this._hass.language || 'es'; const isEn = lang.startsWith('en');
    const valFormulaNueva = this._hass.states['text.nombre_nueva_formula']?.state || '';
    const valHarinaNueva = this._hass.states['text.nombre_nueva_harina']?.state || '';
    const selectorRetirarHarina = this._hass.states['select.porcentaje_panadero_pan_select_retirar_harina_del_inventario'];
    const harinaSeleccionadaRetirar = selectorRetirarHarina?.state || '';
    const opcionesRetirarHarina = selectorRetirarHarina?.attributes['options'] || [];

    if (!this._htmlInyectado) {
      const titleYaml = this.config && this.config.title ? `<div style="font-size: 24px; font-weight: normal; color: var(--primary-text-color); margin-bottom: 16px; padding: 4px 0 12px 0;">${this.config.title}</div>` : '';

      this.content.innerHTML = `
        ${titleYaml}
        <div class="sub-seccion">${isEn ? 'ADD NEW FORMULA' : 'AÑADIR FÓRMULA NUEVA'}</div>
        <div class="fila-inline"><input type="text" class="input-text-pan" id="input-formula-nueva" placeholder="${isEn ? 'Formula name...' : 'Nombre de la fórmula...'}" value="${valFormulaNueva}"><button class="btn-guardar" id="btn-guardar-formula-nueva">💾 ${isEn ? 'SAVE' : 'GUARDAR'}</button></div>
        <div class="divider"></div>
        <div class="sub-seccion" style="border-left-color: #2196f3;">${isEn ? 'CURRENT FORMULA MANAGEMENT' : 'GESTIÓN DE FÓRMULA SELECCIONADA'}</div>
        <div class="btn-gestion-bloque"><button style="background-color: #2196f3;" id="btn-actualizar-formula">💾 ${isEn ? 'UPDATE / SAVE' : 'ACTUALIZAR / GUARDAR'}</button><button style="background-color: var(--error-color, #db4437);" id="btn-eliminar-formula">❌ ${isEn ? 'DELETE' : 'ELIMINAR'}</button></div>
        <div class="divider"></div>
        <div class="sub-seccion" style="border-left-color: var(--success-color, #4caf50);">${isEn ? 'REGISTER FLOUR IN DATABASE' : 'REGISTRAR HARINA EN LA BASE DE DATOS'}</div>
        <div class="fila-inline"><input type="text" class="input-text-pan" id="input-harina-nueva" placeholder="${isEn ? 'Brand / Type...' : 'Marca / Tipo de harina...'}" value="${valHarinaNueva}"><button class="btn-guardar" id="btn-anadir-harina">💾 ${isEn ? 'SAVE' : 'GUARDAR'}</button></div>
        <div class="divider"></div>
        <div class="sub-seccion" style="border-left-color: var(--error-color, #db4437);">${isEn ? 'DELETE FLOUR FROM DATABASE' : 'ELIMINAR HARINA DE LA BASE DE DATOS'}</div>
        <select id="select-retirar-harina"></select><button class="btn-eliminar" style="width: 100%; height: 42px;" id="btn-eliminar-harina-inv">❌ ${isEn ? 'DELETE SELECTED' : 'ELIMINAR HARINA SELECCIONADA'}</button>
      `;
      this.registrarEventosPanelGral(); this._htmlInyectado = true;
    }

    const activeEl = this.shadowRoot.activeElement;
    const inpForm = this.shadowRoot.getElementById('input-formula-nueva'); if (inpForm && inpForm !== activeEl) inpForm.value = valFormulaNueva;
    const inpHar = this.shadowRoot.getElementById('input-harina-nueva'); if (inpHar && inpHar !== activeEl) inpHar.value = valHarinaNueva;

    const selRetHar = this.shadowRoot.getElementById('select-retirar-harina');
    if (selRetHar && selRetHar !== activeEl) {
      selRetHar.innerHTML = `<option value="">${isEn ? 'Select flour to delete...' : 'Selecciona harina a eliminar...'}</option>` + 
        opcionesRetirarHarina.map(opt => `<option value="${opt}" ${opt === harinaSeleccionadaRetirar ? 'selected' : ''}>${opt}</option>`).join('');
    }
  }

  registrarEventosPanelGral() {
    this.shadowRoot.getElementById('input-formula-nueva').addEventListener('change', (e) => { this._hass.callService('text', 'set_value', { entity_id: 'text.nombre_nueva_formula', value: e.target.value }); });
    this.shadowRoot.getElementById('input-harina-nueva').addEventListener('change', (e) => { this._hass.callService('text', 'set_value', { entity_id: 'text.nombre_nueva_harina', value: e.target.value }); });
    this.shadowRoot.getElementById('select-retirar-harina').addEventListener('change', (e) => { this._hass.callService('select', 'select_option', { entity_id: 'select.porcentaje_panadero_pan_select_retirar_harina_del_inventario', option: e.target.value }); });

    this.shadowRoot.getElementById('btn-guardar-formula-nueva').addEventListener('click', () => { this._hass.callService('porcentaje_panadero', 'guardar_formula'); });
    this.shadowRoot.getElementById('btn-actualizar-formula').addEventListener('click', () => { this._hass.callService('porcentaje_panadero', 'confirmar_sobreescritura'); });
    this.shadowRoot.getElementById('btn-eliminar-formula').addEventListener('click', () => { this._hass.callService('porcentaje_panadero', 'confirmar_eliminacion'); });
    this.shadowRoot.getElementById('btn-anadir-harina').addEventListener('click', () => { this._hass.callService('porcentaje_panadero', 'anadir_harina'); });
    this.shadowRoot.getElementById('btn-eliminar-harina-inv').addEventListener('click', () => { this._hass.callService('porcentaje_panadero', 'eliminar_harina'); });
  }
  getCardSize() { return 10; }
}
customElements.define('porcentaje-panadero-control-panel-card', PorcentajePanaderoControlPanelCard);




class PorcentajePanaderoControlTermicoCard extends HTMLElement {
  constructor() { 
    super(); 
    this.attachShadow({ mode: 'open' }); 
    this._htmlInyectado = false;
  }
  
  set hass(hass) { 
    this._hass = hass; 
    if (!this.content) this.initCard(); 
    this.updateCard(); 
  }
  
  setConfig(config) { 
    this.config = config; 
  }

  initCard() {
    const style = document.createElement('style');
    style.textContent = `
      ha-card { padding: 16px; font-family: var(--paper-font-body1_-_font-family, inherit); box-sizing: border-box; }
      .main-title { font-size: 16px; font-weight: bold; color: var(--primary-text-color); display: flex; align-items: center; gap: 8px; margin-bottom: 16px; }
      .main-title ha-icon { color: var(--error-color, #db4437); }
      
      .section-divider { border-top: 1px solid var(--divider-color, #e0e0e0); margin: 20px 0 12px 0; padding-top: 12px; font-size: 13px !important; font-weight: bold; color: var(--primary-color); letter-spacing: 1px; text-transform: uppercase; }
      .section-divider:first-of-type { border-top: none; margin-top: 0; padding-top: 0; }
      
      .tile-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; margin-bottom: 8px; border-radius: 12px; background-color: var(--card-background-color, #fff); border: 1px solid var(--divider-color, rgba(0,0,0,0.1)); gap: 12px; }
      .tile-row-select { flex-direction: column; align-items: flex-start; gap: 6px; }
      .tile-info { flex: 1; display: flex; flex-direction: column; min-width: 0; }
      .tile-name { font-size: 14px; font-weight: 500; color: var(--secondary-text-color); text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      .tile-state { font-size: 1.2rem; font-weight: bold; color: var(--primary-text-color); margin-top: 2px; }
      
      /* Reducido el control al 40% fijo con botones +- igual que en la calculadora */
      .tile-control { width: 40%; display: flex; align-items: center; gap: 6px; }
      .custom-slider-input { flex: 1; height: 20px; display: block !important; opacity: 1 !important; visibility: visible !important; cursor: pointer; min-width: 0; }
      .btn-step { background-color: var(--secondary-background-color, #eee); color: var(--primary-text-color); border: none; width: 26px; height: 26px; border-radius: 6px; font-size: 14px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; user-select: none; flex-shrink: 0; }
      .btn-step:active { background-color: var(--divider-color, #ccc); }
      
      .tile-select { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--divider-color, #ccc); background-color: var(--card-background-color, #fff); color: var(--primary-text-color); font-size: 14px; font-weight: bold; cursor: pointer; width: 100%; box-sizing: border-box; }
      .badge-status { font-size: 13px; font-weight: bold; color: var(--primary-color); text-transform: uppercase; }
      .color-primary { color: #2196f3 !important; }
    `;
    const card = document.createElement('ha-card'); 
    this.content = document.createElement('div');
    card.appendChild(this.content); 
    this.shadowRoot.appendChild(style); 
    this.shadowRoot.appendChild(card);
  }

  updateCard() {
    if (!this._hass) return;

    const lang = this._hass.language || 'es', isEn = lang.startsWith('en');
    const sensorFisico = this._hass.states['sensor.sensor_ficico_instalado']?.state === 'true' || this._hass.states['sensor.sensor_fisico_instalado']?.state === 'true';
    const origenLevado = this._hass.states['select.origen_temperatura_levado']?.state || 'Manual (Slider)';
    const pctPrefermento = parseFloat(this._hass.states['number.prefermento']?.state || 0);

    if (!this._htmlInyectado) {
      const titleYaml = this.config && this.config.title ? `<div style="font-size: 24px; font-weight: normal; color: var(--primary-text-color); margin-bottom: 16px; padding: 4px 0 12px 0;">${this.config.title}</div>` : '';
      
      const secAgua = isEn ? 'IDEAL WATER TEMPERATURE' : 'TEMPERATURA IDEAL DEL AGUA';
      const secLevado = isEn ? 'PROOFING TEMPERATURE' : 'TEMPERATURA DE LEVADO';

      this.content.innerHTML = `
        ${titleYaml}
        <div class="section-divider"><span>${secAgua}</span></div>
        <div id="contenedor-masa"></div>
        <div id="contenedor-ambiente-agua"></div>
        <div id="contenedor-harina"></div>
        <div id="contenedor-prefermento"></div>
        <div id="contenedor-amasadora"></div>
        
        <div class="section-divider"><span>${secLevado}</span></div>
        <div id="contenedor-origen-select"></div>
        <div id="contenedor-ambiente-levado"></div>
      `;
      
      this._htmlInyectado = true;
    }

    const actualizarSelectFila = (contenedorId, nombre, entidad) => {
      const targetDiv = this.shadowRoot.getElementById(contenedorId);
      if (!targetDiv) return;
      
      const entState = this._hass.states[entidad];
      if (!entState) { targetDiv.style.display = 'none'; return; }
      
      const opciones = entState.attributes['options'] || [];
      const valorSeleccionado = entState.state || '---';
      const selectExistente = targetDiv.querySelector('.tile-select');

      if (!selectExistente) {
        targetDiv.innerHTML = `
          <div class="tile-row tile-row-select">
            <span class="tile-name">${nombre}</span>
            <select class="tile-select">
              ${opciones.map(opt => `<option value="${opt}" ${opt === valorSeleccionado ? 'selected' : ''}>${opt.toUpperCase()}</option>`).join('')}
            </select>
          </div>
        `;
        targetDiv.querySelector('.tile-select').addEventListener('change', (e) => {
          this._hass.callService('select', 'select_option', { entity_id: entidad, option: e.target.value });
        });
      } else {
        if (this.shadowRoot.activeElement !== selectExistente && selectExistente.value !== valorSeleccionado) {
          selectExistente.value = valorSeleccionado;
        }
      }
    };

    const actualizarSliderFila = (contenedorId, nombre, entidad, sufijo = ' °C', manualStep = null) => {
      const targetDiv = this.shadowRoot.getElementById(contenedorId);
      if (!targetDiv) return;
      
      const entState = this._hass.states[entidad];
      if (!entState || entState.state === undefined) { targetDiv.style.display = 'none'; return; }
      
      const val = parseFloat(entState.state);
      const min = entState.attributes.min !== undefined ? entState.attributes.min : 0;
      const max = entState.attributes.max !== undefined ? entState.attributes.max : 40;
      const step = manualStep !== null ? manualStep : (entState.attributes.step !== undefined ? entState.attributes.step : 0.5);
      
      const sliderExistente = targetDiv.querySelector('.custom-slider-input');
      
      if (!sliderExistente) {
        targetDiv.innerHTML = `
          <div class="tile-row">
            <div class="tile-info"><span class="tile-name">${nombre}</span><span class="tile-state">${val}${sufijo}</span></div>
            <div class="tile-control">
              <button class="btn-step btn-minus">−</button>
              <input type="range" class="custom-slider-input" min="${min}" max="${max}" step="${step}" value="${val}">
              <button class="btn-step btn-plus">+</button>
            </div>
          </div>
        `;
        
        const inputEl = targetDiv.querySelector('.custom-slider-input');
        const stateEl = targetDiv.querySelector('.tile-state');
        
        const enviarServicio = (nuevoValor) => {
          if (nuevoValor < min) nuevoValor = min;
          if (nuevoValor > max) nuevoValor = max;
          
          const stepStr = step.toString();
          const decimales = stepStr.includes('.') ? stepStr.split('.').length : 0;
          nuevoValor = parseFloat(nuevoValor.toFixed(decimales));
          
          stateEl.textContent = `${nuevoValor}${sufijo}`;
          inputEl.value = nuevoValor;
          this._hass.callService('number', 'set_value', { entity_id: entidad, value: nuevoValor });
        };

        inputEl.addEventListener('input', (e) => {
          enviarServicio(parseFloat(e.target.value));
        });

        targetDiv.querySelector('.btn-minus').addEventListener('click', () => {
          enviarServicio(parseFloat(inputEl.value) - step);
        });

        targetDiv.querySelector('.btn-plus').addEventListener('click', () => {
          enviarServicio(parseFloat(inputEl.value) + step);
        });
      } else {
        const nameEl = targetDiv.querySelector('.tile-name');
        if (nameEl && nameEl.textContent !== nombre) nameEl.textContent = nombre;

        if (this.shadowRoot.activeElement !== sliderExistente) {
          sliderExistente.value = val;
          const stateEl = targetDiv.querySelector('.tile-state');
          if (stateEl) stateEl.textContent = `${val}${sufijo}`;
        }
      }
    };

    actualizarSliderFila('contenedor-masa', isEn ? 'DOUGH TEMP.' : 'TEMP. MASA', 'number.temperatura_objetivo_masa');

    const divAmbAgua = this.shadowRoot.getElementById('contenedor-ambiente-agua');
    if (divAmbAgua) {
      const lblAmb = isEn ? 'AMBIENT TEMP.' : 'TEMP. AMBIENTE';
      if (!sensorFisico) {
        if (divAmbAgua) divAmbAgua.style.display = 'block';
        actualizarSliderFila('contenedor-ambiente-agua', lblAmb, 'number.temperatura_ambiente');
      } else {
        if (divAmbAgua) divAmbAgua.style.display = 'block';
        const tAmbSens = this._hass.states['sensor.temperatura_real']?.state || '0';
        const lblSens = isEn ? 'PHYSICAL SENSOR' : 'SENSOR FÍSICO';
        divAmbAgua.innerHTML = `
          <div class="tile-row">
            <div class="tile-info"><span class="tile-name">${lblAmb}</span><span class="tile-state">${tAmbSens} °C</span></div>
            <div class="badge-status">${lblSens}</div>
          </div>
        `;
      }
    }

    actualizarSliderFila('contenedor-harina', isEn ? 'FLOUR TEMP.' : 'TEMP. HARINA', 'number.temperatura_harina');

    const divPref = this.shadowRoot.getElementById('contenedor-prefermento');
    if (divPref) {
      if (pctPrefermento > 0) {
        if (divPref) divPref.style.display = 'block';
        actualizarSliderFila('contenedor-prefermento', isEn ? 'PREFERMENT TEMP.' : 'TEMP. PREFERMENTO', 'number.temperatura_prefermento');
      } else {
        if (divPref) divPref.style.display = 'none';
      }
    }

    actualizarSliderFila('contenedor-amasadora', isEn ? 'MIXER TEMP.' : 'TEMP. AMASADORA', 'number.temperatura_friccion_amasadora');

    const divOrigen = this.shadowRoot.getElementById('contenedor-origen-select');
    if (divOrigen) {
      if (sensorFisico) {
        if (divOrigen) divOrigen.style.display = 'block';
        const lblSel = isEn ? 'Select temperature source' : 'Selecciona origen de temperatura';
        actualizarSelectFila('contenedor-origen-select', lblSel, 'select.origen_temperatura_levado');
      } else {
        if (divOrigen) divOrigen.style.display = 'none';
      }
    }

    const divAmbLevado = this.shadowRoot.getElementById('contenedor-ambiente-levado');
    if (divAmbLevado) {
      const lblAmb = isEn ? 'AMBIENT TEMP.' : 'TEMP. AMBIENTE';
      if (sensorFisico) {
        if (divAmbLevado) divAmbLevado.style.display = 'block';
        if (origenLevado === 'Sensor Físico') {
          const tReal = this._hass.states['sensor.temperatura_real']?.state || '0';
          const lblReal = isEn ? 'REAL READING' : 'LECTURA REAL';
          divAmbLevado.innerHTML = `
            <div class="tile-row">
              <div class="tile-info"><span class="tile-name">${lblAmb}</span><span class="tile-state">${tReal} °C</span></div>
              <div class="badge-status">${lblReal}</div>
            </div>
          `;
        } else if (origenLevado === 'Manual (Slider)') {
          actualizarSliderFila('contenedor-ambiente-levado', isEn ? 'MANUAL ADJUST' : 'AJUSTE MANUAL', 'number.temperatura_ambiente');
        }
      } else {
        if (divAmbLevado) divAmbLevado.style.display = 'block';
        actualizarSliderFila('contenedor-ambiente-levado', lblAmb, 'number.temperatura_ambiente');
      }
    }
  }

  getCardSize() { return 6; }
}

customElements.define('porcentaje-panadero-control-termico-card', PorcentajePanaderoControlTermicoCard);




class PorcentajePanaderoCalculadoraCard extends HTMLElement {
  constructor() { 
    super(); 
    this.attachShadow({ mode: 'open' }); 
    this._htmlInyectado = false;
  }
  
  set hass(hass) { 
    this._hass = hass; 
    if (!this.content) this.initCard(); 
    this.updateCard(); 
  }
  
  setConfig(config) { 
    this.config = config; 
  }

  initCard() {
    const style = document.createElement('style');
    style.textContent = `
      ha-card { padding: 16px; font-family: var(--paper-font-body1_-_font-family, inherit); box-sizing: border-box; }
      
      .section-divider { border-top: 1px solid var(--divider-color, #e0e0e0); margin: 20px 0 12px 0; padding-top: 12px; font-size: 13px !important; font-weight: bold; letter-spacing: 1px; text-transform: uppercase; display: flex; align-items: center; gap: 6px; }
      .section-divider:first-of-type { border-top: none; margin-top: 0; padding-top: 0; }
      .section-divider ha-icon { color: inherit; }
      
      .tile-row { display: flex; justify-content: space-between; align-items: center; padding: 12px; margin-bottom: 8px; border-radius: 12px; background-color: var(--card-background-color, #fff); border: 1px solid var(--divider-color, rgba(0,0,0,0.1)); gap: 12px; }
      .tile-row-select { flex-direction: column; align-items: flex-start; gap: 6px; }
      .tile-info { flex: 1; display: flex; flex-direction: column; min-width: 0; }
      .tile-name { font-size: 14px; font-weight: 500; color: var(--secondary-text-color); text-transform: uppercase; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
      
      /* El número del porcentaje vuelve a ser grande de forma unificada */
      .tile-state { font-size: 1.2rem; font-weight: bold; color: var(--primary-text-color); margin-top: 2px; }
      
      /* Ajuste específico para reducir un pelín el texto de TIPO DE LEVADURA (FRESCA / SECA) */
      .tile-state-leva-tipo { font-size: 1.05rem !important; font-weight: bold; margin-top: 2px; text-transform: uppercase; }
      
      .tile-control { width: 40%; display: flex; align-items: center; gap: 6px; }
      .custom-slider-input { flex: 1; height: 20px; display: block !important; opacity: 1 !important; visibility: visible !important; cursor: pointer; min-width: 0; }
      .btn-step { background-color: var(--secondary-background-color, #eee); color: var(--primary-text-color); border: none; width: 26px; height: 26px; border-radius: 6px; font-size: 14px; font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; user-select: none; flex-shrink: 0; }
      .btn-step:active { background-color: var(--divider-color, #ccc); }
      
      .tile-select { width: 100%; padding: 10px; border-radius: 8px; border: 1px solid var(--divider-color, #ccc); background-color: var(--card-background-color, #fff); color: var(--primary-text-color); font-size: 14px; font-weight: bold; cursor: pointer; width: 100%; box-sizing: border-box; }
      .badge-status { font-size: 13px; font-weight: bold; text-transform: uppercase; }
      .btn-tile-action { color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 13px; text-transform: uppercase; transition: opacity 0.1s ease; }
      .btn-tile-action:active { opacity: 0.8; }
      
      .color-green { color: #4caf50 !important; }
      .color-orange { color: #ff9800 !important; }
      .color-primary { color: #2196f3 !important; }
      .color-indigo { color: #3f51b5 !important; }
      .color-deep-orange { color: #ff5722 !important; }
      
      .btn-primary { background-color: #2196f3; }
      .btn-indigo { background-color: #3f51b5; }
      .btn-deep-orange { background-color: #ff5722; }
      
      .badge-primary { color: #2196f3; }
      .badge-indigo { color: #3f51b5; }
      
      .slider-green { accent-color: #4caf50 !important; }
      .slider-orange { accent-color: #ff9800 !important; }
      .slider-primary { accent-color: #2196f3 !important; }
      .slider-indigo { accent-color: #3f51b5 !important; }
      .slider-deep-orange { accent-color: #ff5722 !important; }
      
      .switch-toggle { position: relative; display: inline-block; width: 44px; height: 24px; flex-shrink: 0; }
      .switch-toggle input { opacity: 0; width: 0; height: 0; }
      .switch-slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: var(--secondary-background-color, #ccc); transition: .2s; border-radius: 24px; }
      .switch-slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .2s; border-radius: 50%; }
      input:checked + .switch-slider { background-color: #ff5722; }
      input:checked + .switch-slider:before { transform: translateX(20px); }
    `;
    const card = document.createElement('ha-card'); 
    this.content = document.createElement('div');
    card.appendChild(this.content); 
    this.shadowRoot.appendChild(style); 
    this.shadowRoot.appendChild(card);
  }

  updateCard() {
    if (!this._hass) return;

    const lang = this._hass.language || 'es', isEn = lang.startsWith('en');

    const prefermentoState = this._hass.states['number.prefermento'];
    const pctPrefermento = prefermentoState ? parseFloat(prefermentoState.state || 0) : 0;
    const tipoPrefReal = (this._hass.states['select.tipo_de_prefermento']?.state || 'poolish').toLowerCase();

    const extrasSwitch = this._hass.states['switch.habilitar_ingredientes_extras'];
    const extrasActivos = extrasSwitch ? extrasSwitch.state === 'on' : false;

    const marcaHarina1 = this._hass.states['select.harina_principal_1']?.state || (isEn ? 'FLOUR 1' : 'HARINA 1');
    const marcaHarina2 = this._hass.states['select.harina_secundaria_2']?.state || (isEn ? 'FLOUR 2' : 'HARINA 2');
    const marcaHarina3 = this._hass.states['select.harina_secundaria_3']?.state || (isEn ? 'FLOUR 3' : 'HARINA 3');

    if (!this._htmlInyectado) {
      const titleYaml = this.config && this.config.title ? `<div style="font-size: 24px; font-weight: normal; color: var(--primary-text-color); margin-bottom: 16px; padding: 4px 0 12px 0;">${this.config.title}</div>` : '';
      
      const secMarcas = isEn ? 'FLOUR FORMULA: BRAND / TYPE' : 'HARINA FÓRMULA: MARCA / TIPO';
      const secPorcentajes = isEn ? 'BAKER PERCENTAGES' : 'PORCENTAJES';
      const secPrefermento = isEn ? 'BIGA / POOLISH / SOURDOUGH' : 'BIGA / POOLISH / MASA MADRE';

      this.content.innerHTML = `
        ${titleYaml}
        <div id="slider-masa-objetivo"></div>

        <div class="section-divider color-orange"><ha-icon icon="mdi:barley"></ha-icon><span>${secMarcas}</span></div>
        <div id="select-h1"></div>
        <div id="select-h2"></div>
        <div id="select-h3"></div>
        
        <div class="section-divider color-orange"><span>${secPorcentajes}</span></div>
        <div id="slider-h1"></div>
        <div id="slider-h2"></div>
        <div id="slider-h3"></div>
        <div id="slider-agua"></div>
        <div id="slider-sal"></div>
        <div id="row-tipo-levadura"></div>
        <div id="slider-leva"></div>
        
        <div class="section-divider color-indigo"><span>${secPrefermento}</span></div>
        <div id="slider-prefermento"></div>
        <div id="select-tipo-prefermento" style="display: none;"></div>
        <div id="slider-leva-prefermento" style="display: none;"></div>
        <div id="slider-inoculo-mm" style="display: none;"></div>
        <div id="slider-hidratacion-mm" style="display: none;"></div>
        <div id="select-harina-prefermento" style="display: none;"></div>
        
        <div class="section-divider color-deep-orange"><span>${isEn ? 'EXTRA INGREDIENTS' : 'INGREDIENTES EXTRAS'}</span></div>
        <div id="row-habilitar-extras"></div>
        
        <div id="slider-malta" style="display: none;"></div>
        <div id="slider-azucar" style="display: none;"></div>
        <div id="slider-leche-polvo" style="display: none;"></div>
        <div id="slider-leche-liquida" style="display: none;"></div>
        <div id="slider-tang-zhong" style="display: none;"></div>
        <div id="row-tz-base-liquida" style="display: none;"></div>
        <div id="slider-huevo" style="display: none;"></div>
        <div id="slider-mantequilla" style="display: none;"></div>
        <div id="slider-aove" style="display: none;"></div>
        <div id="row-calcular-hidratacion-real" style="display: none;"></div>
      `;
      
      this._htmlInyectado = true;
    }

    const actualizarSelectFila = (contenedorId, nombre, entidad) => {
      const targetDiv = this.shadowRoot.getElementById(contenedorId);
      if (!targetDiv) return;
      
      const entState = this._hass.states[entidad];
      if (!entState) { targetDiv.style.display = 'none'; return; }
      
      const opciones = entState.attributes['options'] || [];
      const valorSeleccionado = entState.state || '---';
      const selectExistente = targetDiv.querySelector('.tile-select');

      if (!selectExistente) {
        targetDiv.innerHTML = `
          <div class="tile-row tile-row-select">
            <span class="tile-name">${nombre}</span>
            <select class="tile-select">
              ${opciones.map(opt => `<option value="${opt}" ${opt === valorSeleccionado ? 'selected' : ''}>${opt.toUpperCase()}</option>`).join('')}
            </select>
          </div>
        `;
        targetDiv.querySelector('.tile-select').addEventListener('change', (e) => {
          this._hass.callService('select', 'select_option', { entity_id: entidad, option: e.target.value });
        });
      } else {
        if (this.shadowRoot.activeElement !== selectExistente && selectExistente.value !== valorSeleccionado) {
          selectExistente.value = valorSeleccionado;
        }
      }
    };

    const actualizarSliderFila = (contenedorId, nombre, entidad, sufijo = '%', manualStep = null, claseColorSlider = 'slider-orange') => {
      const targetDiv = this.shadowRoot.getElementById(contenedorId);
      if (!targetDiv) return;
      
      const entState = this._hass.states[entidad];
      if (!entState || entState.state === undefined) { targetDiv.style.display = 'none'; return; }
      
      const val = parseFloat(entState.state);
      const min = entState.attributes.min !== undefined ? entState.attributes.min : 0;
      const max = entState.attributes.max !== undefined ? entState.attributes.max : 100;
      const step = manualStep !== null ? manualStep : (entState.attributes.step !== undefined ? entState.attributes.step : 1);
      
      const sliderExistente = targetDiv.querySelector('.custom-slider-input');
      
      if (!sliderExistente) {
        targetDiv.innerHTML = `
          <div class="tile-row">
            <div class="tile-info"><span class="tile-name">${nombre}</span><span class="tile-state">${val} ${sufijo}</span></div>
            <div class="tile-control">
              <button class="btn-step btn-minus">−</button>
              <input type="range" class="custom-slider-input ${claseColorSlider}" min="${min}" max="${max}" step="${step}" value="${val}">
              <button class="btn-step btn-plus">+</button>
            </div>
          </div>
        `;
        
        const inputEl = targetDiv.querySelector('.custom-slider-input');
        const stateEl = targetDiv.querySelector('.tile-state');
        
        const enviarServicio = (nuevoValor) => {
          if (nuevoValor < min) nuevoValor = min;
          if (nuevoValor > max) nuevoValor = max;
          
          const stepStr = step.toString();
          const decimales = stepStr.includes('.') ? stepStr.split('.').length : 0;
          nuevoValor = parseFloat(nuevoValor.toFixed(decimales));
          
          stateEl.textContent = `${nuevoValor} ${sufijo}`;
          inputEl.value = nuevoValor;
          this._hass.callService('number', 'set_value', { entity_id: entidad, value: nuevoValor });
        };

        inputEl.addEventListener('input', (e) => {
          enviarServicio(parseFloat(e.target.value));
        });

        targetDiv.querySelector('.btn-minus').addEventListener('click', () => {
          enviarServicio(parseFloat(inputEl.value) - step);
        });

        targetDiv.querySelector('.btn-plus').addEventListener('click', () => {
          enviarServicio(parseFloat(inputEl.value) + step);
        });
      } else {
        const nameEl = targetDiv.querySelector('.tile-name');
        if (nameEl && nameEl.textContent !== nombre) nameEl.textContent = nombre;

        if (this.shadowRoot.activeElement !== sliderExistente) {
          sliderExistente.value = val;
          const stateEl = targetDiv.querySelector('.tile-state');
          if (stateEl) stateEl.textContent = `${val} ${sufijo}`;
        }
      }
    };

    actualizarSliderFila('slider-masa-objetivo', isEn ? 'TOTAL DOUGH WEIGHT' : 'CANTIDAD DE MASA', 'number.masa_final_objetivo', 'g', 50, 'slider-green');
    actualizarSelectFila('select-h1', isEn ? 'FLOUR TYPE 1' : 'HARINA 1', 'select.harina_principal_1');
    actualizarSelectFila('select-h2', isEn ? 'FLOUR TYPE 2' : 'HARINA 2', 'select.harina_secundaria_2');
    actualizarSelectFila('select-h3', isEn ? 'FLOUR TYPE 3' : 'HARINA 3', 'select.harina_secundaria_3');

    actualizarSliderFila('slider-h1', marcaHarina1.toUpperCase(), 'number.harina_1', '%', null, 'slider-orange');
    actualizarSliderFila('slider-h2', marcaHarina2.toUpperCase(), 'number.harina_2', '%', null, 'slider-orange');
    actualizarSliderFila('slider-h3', marcaHarina3.toUpperCase(), 'number.harina_3', '%', null, 'slider-orange');
    actualizarSliderFila('slider-agua', isEn ? 'WATER' : 'AGUA', 'number.agua_hidratacion', '%', null, 'slider-orange');
    actualizarSliderFila('slider-sal', isEn ? 'SALT' : 'SAL', 'number.sal', '%', null, 'slider-orange');

    const divTipoLeva = this.shadowRoot.getElementById('row-tipo-levadura');
    if (divTipoLeva) {
      const btnState = this._hass.states['button.alternar_fresca_seca'];
      if (btnState) {
        const estadoActual = (btnState.state || 'fresca').toUpperCase();
        divTipoLeva.innerHTML = `
          <div class="tile-row">
            <div class="tile-info"><span class="tile-name">${isEn ? 'YEAST TYPE' : 'TIPO LEVADURA'}</span><span class="tile-state-leva-tipo color-orange">${estadoActual}</span></div>
            <button class="btn-tile-action" style="background-color:#ff9800;">${isEn ? 'TOGGLE' : 'ALTERNAR'}</button>
          </div>
        `;
        divTipoLeva.querySelector('.btn-tile-action').addEventListener('click', () => {
          this._hass.callService('button', 'press', { entity_id: 'button.alternar_fresca_seca' });
        });
      }
    }

    actualizarSliderFila('slider-leva', isEn ? 'YEAST' : 'LEVADURA', 'number.levadura', '%', null, 'slider-orange');

    actualizarSliderFila('slider-prefermento', isEn ? 'PREFERMENT' : 'PREFERMENTO', 'number.prefermento', '%', null, 'slider-indigo');

    const divTipoPref = this.shadowRoot.getElementById('select-tipo-prefermento');
    const divLevaPref = this.shadowRoot.getElementById('slider-leva-prefermento');
    const divInoculo = this.shadowRoot.getElementById('slider-inoculo-mm');
    const divHidratMM = this.shadowRoot.getElementById('slider-hidratacion-mm');
    const divHarinaPref = this.shadowRoot.getElementById('select-harina-prefermento');

    if (pctPrefermento > 0) {
      if (divTipoPref) divTipoPref.style.display = 'block';
      if (divHarinaPref) divHarinaPref.style.display = 'block';

      actualizarSelectFila('select-tipo-prefermento', isEn ? 'PREFERMENT TYPE' : 'TIPO PREFERMENTO', 'select.tipo_de_prefermento');

      if (tipoPrefReal !== 'masa madre') {
        if (divLevaPref) divLevaPref.style.display = 'block';
        actualizarSliderFila('slider-leva-prefermento', isEn ? 'PREFERMENT YEAST' : 'LEVADURA PREFERMENTO', 'number.levadura_prefermento', '%', null, 'slider-indigo');
        if (divInoculo) divInoculo.style.display = 'none';
        if (divHidratMM) divHidratMM.style.display = 'none';
      } else {
        if (divLevaPref) divLevaPref.style.display = 'none';
        if (divInoculo) divInoculo.style.display = 'block';
        if (divHidratMM) divHidratMM.style.display = 'block';
        actualizarSliderFila('slider-inoculo-mm', isEn ? 'SOURDOUGH INOCULUM' : 'INÓCULO MASA MADRE', 'number.inoculo_masa_madre', '%', null, 'slider-indigo');
        actualizarSliderFila('slider-hidratacion-mm', isEn ? 'SOURDOUGH HYDRATION' : 'HIDRATACIÓN MASA MADRE', 'number.hidratacion_masa_madre', '%', null, 'slider-indigo');
      }

      actualizarSelectFila('select-harina-prefermento', isEn ? 'PREFERMENT FLOUR' : 'HARINA PREFERMENTO', 'select.harina_para_prefermento');
    } else {
      if (divTipoPref) divTipoPref.style.display = 'none';
      if (divLevaPref) divLevaPref.style.display = 'none';
      if (divInoculo) divInoculo.style.display = 'none';
      if (divHidratMM) divHidratMM.style.display = 'none';
      if (divHarinaPref) divHarinaPref.style.display = 'none';
    }

    const divHabilitarExtras = this.shadowRoot.getElementById('row-habilitar-extras');
    if (divHabilitarExtras) {
      const isChecked = extrasActivos ? 'checked' : '';
      divHabilitarExtras.innerHTML = `
        <div class="tile-row">
          <div class="tile-info"><span class="tile-name">${isEn ? 'EXTRAS' : 'EXTRAS'}</span></div>
          <label class="switch-toggle"><input type="checkbox" id="chk-extras" ${isChecked}><span class="switch-slider"></span></label>
        </div>
      `;
      divHabilitarExtras.querySelector('#chk-extras').addEventListener('change', (e) => {
        this._hass.callService('switch', e.target.checked ? 'turn_on' : 'turn_off', { entity_id: 'switch.habilitar_ingredientes_extras' });
      });
    }

    const divMalta = this.shadowRoot.getElementById('slider-malta');
    const divAzucar = this.shadowRoot.getElementById('slider-azucar');
    const divLecheP = this.shadowRoot.getElementById('slider-leche-polvo');
    const divLecheL = this.shadowRoot.getElementById('slider-leche-liquida');
    const divTZ = this.shadowRoot.getElementById('slider-tang-zhong');
    const divTZBase = this.shadowRoot.getElementById('row-tz-base-liquida');
    const divHuevo = this.shadowRoot.getElementById('slider-huevo');
    const divMantequilla = this.shadowRoot.getElementById('slider-mantequilla');
    const divAove = this.shadowRoot.getElementById('slider-aove');
    const divHidratReal = this.shadowRoot.getElementById('row-calcular-hidratacion-real');

    if (extrasActivos) {
      if (divMalta) divMalta.style.display = 'block';
      if (divAzucar) divAzucar.style.display = 'block';
      if (divLecheP) divLecheP.style.display = 'block';
      if (divLecheL) divLecheL.style.display = 'block';
      if (divTZ) divTZ.style.display = 'block';
      if (divHuevo) divHuevo.style.display = 'block';
      if (divMantequilla) divMantequilla.style.display = 'block';
      if (divAove) divAove.style.display = 'block';

      actualizarSliderFila('slider-malta', isEn ? 'MALT' : 'MALTA', 'number.malta', '%', null, 'slider-deep-orange');
      actualizarSliderFila('slider-azucar', isEn ? 'SUGAR' : 'AZÚCAR', 'number.azucar', '%', null, 'slider-deep-orange');
      actualizarSliderFila('slider-leche-polvo', isEn ? 'MILK POWDER 26%' : 'LECHE EN POLVO', 'number.leche_en_polvo', '%', null, 'slider-deep-orange');
      actualizarSliderFila('slider-leche-liquida', isEn ? 'MILK' : 'LECHE', 'number.leche_liquida', '%', null, 'slider-deep-orange');
      actualizarSliderFila('slider-tang-zhong', isEn ? 'TANG-ZHONG' : 'TANG-ZHONG', 'number.tang_zhong', '%', null, 'slider-deep-orange');

      const valLecheLiq = parseFloat(this._hass.states['number.leche_liquida']?.state || 0);
      const valHuevo = parseFloat(this._hass.states['number.huevo']?.state || 0);
      const valTZ = parseFloat(this._hass.states['number.tang_zhong']?.state || 0);

      if (valTZ > 0 && valLecheLiq > 0) {
        if (divTZBase) divTZBase.style.display = 'block';
        const btnTZBase = this._hass.states['button.alternar_tang_zhong_agua_leche'];
        if (btnTZBase) {
          const estadoTZBase = (btnTZBase.attributes['base_liquida'] || btnTZBase.state || 'agua').toUpperCase();
          divTZBase.innerHTML = `
            <div class="tile-row">
              <div class="tile-info"><span class="tile-name">${isEn ? 'TANG-ZHONG BASE' : 'TANG-ZHONG BASE'}</span><span class="tile-state color-deep-orange">${estadoTZBase}</span></div>
              <button class="btn-tile-action btn-deep-orange">${isEn ? 'TOGGLE' : 'ALTERNAR'}</button>
            </div>
          `;
          divTZBase.querySelector('.btn-tile-action').addEventListener('click', () => {
            this._hass.callService('button', 'press', { entity_id: 'button.alternar_tang_zhong_agua_leche' });
          });
        }
      } else {
        if (divTZBase) divTZBase.style.display = 'none';
      }

      actualizarSliderFila('slider-huevo', isEn ? 'EGG' : 'HUEVO', 'number.huevo', '%', null, 'slider-deep-orange');
      actualizarSliderFila('slider-mantequilla', isEn ? 'BUTTER' : 'MANTEQUILLA', 'number.mantequilla', '%', null, 'slider-deep-orange');
      actualizarSliderFila('slider-aove', isEn ? 'EVOO' : 'AOVE', 'number.aove', '%', null, 'slider-deep-orange');

      if (valLecheLiq > 0 || valHuevo > 0) {
        if (divHidratReal) divHidratReal.style.display = 'block';
        const swHidratReal = this._hass.states['switch.calcular_hidratacion_real'];
        if (swHidratReal) {
          const isHidratChecked = swHidratReal.state === 'on' ? 'checked' : '';
          divHidratReal.innerHTML = `
            <div class="tile-row">
              <div class="tile-info"><span class="tile-name">${isEn ? 'CALC. REAL HYDRATION' : 'CAL. HIDRATACIÓN REAL'}</span></div>
              <label class="switch-toggle"><input type="checkbox" id="chk-hidrat-real" ${isHidratChecked}><span class="switch-slider"></span></label>
            </div>
          `;
          divHidratReal.querySelector('#chk-hidrat-real').addEventListener('change', (e) => {
            this._hass.callService('switch', e.target.checked ? 'turn_on' : 'turn_off', { entity_id: 'switch.calcular_hidratacion_real' });
          });
        }
      } else {
        if (divHidratReal) divHidratReal.style.display = 'none';
      }
    } else {
      if (divMalta) divMalta.style.display = 'none';
      if (divAzucar) divAzucar.style.display = 'none';
      if (divLecheP) divLecheP.style.display = 'none';
      if (divLecheL) divLecheL.style.display = 'none';
      if (divTZ) divTZ.style.display = 'none';
      if (divTZBase) divTZBase.style.display = 'none';
      if (divHuevo) divHuevo.style.display = 'none';
      if (divMantequilla) divMantequilla.style.display = 'none';
      if (divAove) divAove.style.display = 'none';
      if (divHidratReal) divHidratReal.style.display = 'none';
    }
  }

  getCardSize() { return 12; }
}

customElements.define('porcentaje-panadero-calculadora-card', PorcentajePanaderoCalculadoraCard);
