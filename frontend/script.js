const API = "https://laika-system.onrender.com";

// ─── HELPERS ─────────────────────────────────────────────────────────────────

function regimeClass(regime) {
    if (!regime) return '';
    const r = regime.toUpperCase();
    if (r === 'ESTOCASTICO') return 'regime-estocastico';
    if (r === 'TRANSICAO')   return 'regime-transicao';
    if (r === 'CAOTICO')     return 'regime-caotico';
    return '';
}

function alertaClass(nivel) {
    if (!nivel) return '';
    const n = nivel.toUpperCase();
    if (n === 'VERMELHO') return 'alerta-nivel-vermelho';
    if (n === 'AMARELO')  return 'alerta-nivel-amarelo';
    if (n === 'VERDE')    return 'alerta-nivel-verde';
    return '';
}

function habitatStatusClass(status) {
    if (!status) return '';
    return status.toUpperCase() === 'ATIVO' ? 'habitat-status-ativo' : 'habitat-status-manutencao';
}

function mostrarFeedback(mensagem, tipo) {
    const box = document.getElementById("feedback-cadastro");
    if (!box) return;
    box.className = `feedback-box feedback-${tipo}`;
    box.textContent = mensagem;
    box.style.display = "block";
    setTimeout(() => { box.style.display = "none"; }, 4000);
}

// ─── LEITURAS ────────────────────────────────────────────────────────────────

async function carregarLeituras() {
    try {
        const resposta = await fetch(`${API}/leituras`);
        const dados = await resposta.json();

        const tabela = document.getElementById("tabela-leituras");
        if (!tabela) return;

        if (dados.length === 0) {
            tabela.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#64748B; padding:32px;">
                Nenhuma leitura registrada ainda. Use o formulário abaixo para inserir a primeira.
            </td></tr>`;
            return;
        }

        tabela.innerHTML = dados.map(leitura => `
            <tr>
                <td><strong>#${leitura.id}</strong></td>
                <td>${leitura.zona}</td>
                <td>${leitura.density_of_maxima} Hz</td>
                <td class="lyapunov-cell">${leitura.lyapunov_estimado}</td>
                <td class="${regimeClass(leitura.regime_classificado)}">${leitura.regime_classificado}</td>
                <td class="actions-cell">
                    <button class="btn-table edit-btn" onclick="editarLeitura(${leitura.id})">Editar</button>
                    <button class="btn-table delete-btn" onclick="deletarLeitura(${leitura.id})">Excluir</button>
                </td>
            </tr>
        `).join('');
    } catch (erro) {
        console.error("Erro ao carregar leituras:", erro);
        const tabela = document.getElementById("tabela-leituras");
        if (tabela) tabela.innerHTML = `<tr><td colspan="6" style="text-align:center; color:#EF4444; padding:20px;">
            Erro ao conectar com a API. Verifique se o servidor FastAPI está rodando em ${API}
        </td></tr>`;
    }
}

async function salvarLeitura() {
    const zonaInput    = document.getElementById("zona");
    const densityInput = document.getElementById("density");
    const lyapunovInput= document.getElementById("lyapunov");
    const regimeInput  = document.getElementById("regime");
    const btn          = document.getElementById("btn-salvar");

    if (!zonaInput.value || !densityInput.value || !lyapunovInput.value) {
        mostrarFeedback("Preencha todos os campos antes de enviar.", "error");
        return;
    }

    btn.disabled = true;
    btn.textContent = "Enviando...";

    try {
        const resp = await fetch(`${API}/leituras`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                zona: zonaInput.value,
                density_of_maxima: parseFloat(densityInput.value),
                lyapunov_estimado: parseFloat(lyapunovInput.value),
                regime_classificado: regimeInput.value
            })
        });

        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);

        const nova = await resp.json();
        mostrarFeedback(`✓ Leitura #${nova.id} registrada com sucesso via POST /leituras`, "success");

        zonaInput.value = "";
        densityInput.value = "";
        lyapunovInput.value = "";

        carregarLeituras();
    } catch (erro) {
        mostrarFeedback("Erro ao enviar leitura. Verifique se a API está ativa.", "error");
        console.error("Erro ao salvar leitura:", erro);
    } finally {
        btn.disabled = false;
        btn.textContent = "Enviar via POST";
    }
}

async function deletarLeitura(id) {
    if (!confirm(`Confirmar exclusão da leitura #${id}? Esta ação chama DELETE /leituras/${id}`)) return;
    try {
        const resp = await fetch(`${API}/leituras/${id}`, { method: "DELETE" });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        carregarLeituras();
    } catch (erro) {
        alert("Erro ao deletar leitura. Verifique a conexão com a API.");
        console.error("Erro ao deletar leitura:", erro);
    }
}

async function editarLeitura(id) {
    const novaZona = prompt(`[PUT /leituras/${id}]\nNova zona / módulo:`);
    if (!novaZona) return;

    const density = parseFloat(prompt("Novo Density of Maxima (Hz):"));
    if (isNaN(density)) return;

    const lyapunov = parseFloat(prompt("Novo Índice de Lyapunov:"));
    if (isNaN(lyapunov)) return;

    const regime = prompt("Novo Regime (ESTOCASTICO, TRANSICAO ou CAOTICO):");
    if (!regime) return;

    try {
        const resp = await fetch(`${API}/leituras/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                zona: novaZona,
                density_of_maxima: density,
                lyapunov_estimado: lyapunov,
                regime_classificado: regime.toUpperCase().trim()
            })
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        carregarLeituras();
    } catch (erro) {
        alert("Erro ao editar leitura.");
        console.error("Erro ao editar leitura:", erro);
    }
}

// ─── ALERTAS ─────────────────────────────────────────────────────────────────

async function carregarAlertas() {
    try {
        const resposta = await fetch(`${API}/alertas`);
        const dados = await resposta.json();

        document.querySelectorAll("#lista-alertas").forEach(container => {
            container.innerHTML = dados.map(alerta => `
                <div class="card">
                    <h4 class="${alertaClass(alerta.nivel)}">${alerta.nivel}</h4>
                    <p>${alerta.descricao}</p>
                    <small>Status: ${alerta.status}</small>
                </div>
            `).join('');
        });
    } catch (erro) {
        console.error("Erro ao carregar alertas:", erro);
    }
}

// ─── HABITATS ────────────────────────────────────────────────────────────────

async function carregarHabitats() {
    try {
        const resposta = await fetch(`${API}/habitats`);
        const dados = await resposta.json();

        document.querySelectorAll("#lista-habitats").forEach(container => {
            container.innerHTML = dados.map(h => `
                <div class="card">
                    <h4>${h.nome}</h4>
                    <p>Operador: ${h.operador}</p>
                    <small class="${habitatStatusClass(h.status)}">● ${h.status}</small>
                </div>
            `).join('');
        });
    } catch (erro) {
        console.error("Erro ao carregar habitats:", erro);
    }
}

// ─── INIT ────────────────────────────────────────────────────────────────────

carregarLeituras();
carregarAlertas();
carregarHabitats();