document.addEventListener('DOMContentLoaded', function() {
    const html = document.documentElement;
    const themeButtons = document.querySelectorAll('.theme-btn');
    const customThemeBtn = document.querySelector('.custom-theme');
    const modal = document.getElementById('customThemeModal');
    const closeModal = document.getElementById('closeModal');
    const applyTheme = document.getElementById('applyTheme');
    const bgOpacitySlider = document.getElementById('bgOpacity');
    
    // Charger le thème sauvegardé
    const savedTheme = localStorage.getItem('theme');
    const savedOpacity = localStorage.getItem('bgOpacity') || '85';
    
    // Appliquer l'opacité sauvegardée si le slider existe
    if (bgOpacitySlider) {
        document.documentElement.style.setProperty('--bg-opacity', savedOpacity / 100);
        bgOpacitySlider.value = savedOpacity;
    }

    if (savedTheme) {
        html.setAttribute('data-theme', savedTheme);
        if (savedTheme === 'custom') {
            applyCustomTheme();
        }
    }

    // Gestionnaire de thème
    themeButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const theme = btn.dataset.theme;
            if (theme !== 'custom') {
                html.setAttribute('data-theme', theme);
                localStorage.setItem('theme', theme);
            }
        });
    });

    // Gestionnaire de l'opacité du fond si le slider existe
    if (bgOpacitySlider) {
        bgOpacitySlider.addEventListener('input', (e) => {
            const opacity = e.target.value / 100;
            document.documentElement.style.setProperty('--bg-opacity', opacity);
            localStorage.setItem('bgOpacity', e.target.value);
        });
    }

    // Gestionnaire du thème personnalisé
    customThemeBtn.addEventListener('click', () => {
        modal.classList.add('active');
    });

    closeModal.addEventListener('click', () => {
        modal.classList.remove('active');
    });

    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });

    // Appliquer le thème personnalisé
    applyTheme.addEventListener('click', () => {
        const bgColor = document.getElementById('bgColor').value;
        const bgOpacity = document.getElementById('bgOpacity').value;
        const textColor = document.getElementById('textColor').value;
        const mutedColor = document.getElementById('mutedColor').value;

        // Convertir la couleur hex en rgba pour le fond
        const rgbaBackground = hexToRGBA(bgColor, bgOpacity / 100);
        
        // Sauvegarder les couleurs personnalisées
        const customColors = {
            bg: rgbaBackground,
            text: textColor,
            muted: mutedColor,
            border: hexToRGBA(mutedColor, 0.4),
            overlay: hexToRGBA(bgColor, bgOpacity / 100)
        };
        localStorage.setItem('customColors', JSON.stringify(customColors));
        localStorage.setItem('bgOpacity', bgOpacity);

        // Appliquer le thème
        html.setAttribute('data-theme', 'custom');
        localStorage.setItem('theme', 'custom');
        applyCustomTheme();
        
        modal.classList.remove('active');
    });

    function applyCustomTheme() {
        const savedColors = JSON.parse(localStorage.getItem('customColors'));
        if (savedColors) {
            document.documentElement.style.setProperty('--custom-bg', savedColors.bg);
            document.documentElement.style.setProperty('--custom-text', savedColors.text);
            document.documentElement.style.setProperty('--custom-muted', savedColors.muted);
            document.documentElement.style.setProperty('--custom-border', savedColors.border);
            document.documentElement.style.setProperty('--custom-overlay', savedColors.overlay);
        }
    }

    function hexToRGBA(hex, alpha = 1) {
        const r = parseInt(hex.slice(1, 3), 16);
        const g = parseInt(hex.slice(3, 5), 16);
        const b = parseInt(hex.slice(5, 7), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
    }
});
