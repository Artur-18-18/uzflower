// Flower Loader Control
(function() {
    let loader = null;

    // Get loader element
    function getLoader() {
        if (loader) return loader;
        loader = document.getElementById('flower-loader');
        return loader;
    }

    // Update loader text based on current language
    function updateLoaderText() {
        const loaderEl = getLoader();
        if (!loaderEl) return;
        
        const textElement = loaderEl.querySelector('.loader-text');
        if (!textElement) return;
        
        // Get current language from i18n system
        const currentLang = localStorage.getItem('uzflower_lang') || 'ru';
        const loadingText = currentLang === 'uz' ? 'Yuklanmoqda...' : 'Загрузка...';
        
        textElement.textContent = loadingText;
    }

    // Show loader
    window.showLoader = function() {
        const loaderEl = getLoader();
        if (loaderEl) {
            updateLoaderText();
            loaderEl.classList.remove('hidden');
            document.body.style.overflow = 'hidden';
        }
    };

    // Hide loader
    window.hideLoader = function() {
        const loaderEl = getLoader();
        if (loaderEl) {
            loaderEl.classList.add('hidden');
            document.body.style.overflow = '';
        }
    };

    // Auto-hide loader on page load
    window.addEventListener('load', function() {
        setTimeout(function() {
            hideLoader();
        }, 1500); // Show for 1.5 seconds
    });

    // Update text when language changes
    document.addEventListener('i18n:languageChanged', function() {
        updateLoaderText();
    });
    
    // Initial text setup
    updateLoaderText();
})();
