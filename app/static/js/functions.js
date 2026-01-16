document.addEventListener('DOMContentLoaded', () => {
    
    const form = document.getElementById('analyzeForm');
    
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // 1. Elementos da UI
        const btnText = document.getElementById('btn-text');
        const btnLoader = document.getElementById('btn-loader');
        
        // Elementos da área de resultado
        const placeholderArea = document.getElementById('placeholder-area');
        const resultArea = document.getElementById('result-area');
        
        // O Overlay de carregamento (NOVO)
        const loaderOverlay = document.getElementById('result-loader-overlay');
        
        // Elementos de texto
        const categoryBadge = document.getElementById('category-badge');
        const responseText = document.getElementById('response-text');

        // 2. Mudar visual para "Carregando"
        // Mostra o spinner do botão
        btnText.classList.add('hidden');
        btnLoader.classList.remove('hidden');
        
        // Mostra o overlay de carregamento na direita
        if (loaderOverlay) {
            loaderOverlay.classList.remove('hidden');
            loaderOverlay.classList.add('flex');
        }

        // Esconde o placeholder e o resultado anterior (se houver)
        // placeholderArea.classList.add('hidden'); // Opcional: manter ou não o fundo
        resultArea.classList.add('hidden');

        const formData = new FormData(this);

        try {
            // Pega a chave do LocalStorage
            const userKey = localStorage.getItem('sortly_gemini_key');
            const headers = {};
            if (userKey) headers['X-Gemini-Key'] = userKey;

            // 3. Enviar para o Backend
            const response = await fetch('/analyze', {
                method: 'POST',
                headers: headers,
                body: formData
            });

            const data = await response.json();

            if (response.ok) {
                // Sucesso: Esconde placeholder
                placeholderArea.classList.add('hidden');
                
                // Mostra a área de resultado
                resultArea.classList.remove('hidden');

                // Preenche os dados
                responseText.textContent = data.resposta_sugerida;
                categoryBadge.textContent = data.categoria;
                
                // Lógica de cores (Verde/Cinza)
                const catLower = data.categoria.toLowerCase();
                if (catLower.includes('produtivo') && !catLower.includes('im')) {
                    categoryBadge.className = "inline-flex items-center px-4 py-2 rounded-lg text-sm font-bold bg-green-100 text-green-800 border border-green-200";
                    categoryBadge.innerHTML = '<i class="ph ph-check-circle mr-2 text-lg"></i> ' + data.categoria;
                } else {
                    categoryBadge.className = "inline-flex items-center px-4 py-2 rounded-lg text-sm font-bold bg-gray-100 text-gray-700 border border-gray-200";
                    categoryBadge.innerHTML = '<i class="ph ph-coffee mr-2 text-lg"></i> ' + data.categoria;
                }

            } else {
                alert('Erro: ' + (data.error || 'Ocorreu um erro desconhecido.'));
            }

        } catch (error) {
            console.error('Erro de conexão:', error);
            alert('Falha ao conectar com o servidor.');
        } finally {
            // 4. LIMPEZA (Isso roda sempre, erro ou sucesso)
            
            // Reseta botão
            btnText.classList.remove('hidden');
            btnLoader.classList.add('hidden');

            // ESCONDE O OVERLAY (Isso destrava a tela)
            if (loaderOverlay) {
                loaderOverlay.classList.add('hidden');
                loaderOverlay.classList.remove('flex');
            }
        }
    });
});