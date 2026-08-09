/**
 * STACORP ONE - ENTERPRISE LOGIN INTERACTIVE CONTROLLER
 * Handles Tab Switching, Background Toggling, Language Switching, 
 * Alert Banners, and Contrast Visual Enhancements.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elements
  const bgLayers = document.querySelectorAll('.bg-layer');
  const bgBtns = document.querySelectorAll('.bg-switcher-btn');
  const tabBtns = document.querySelectorAll('.tab-btn');
  const tabPanels = document.querySelectorAll('.tab-content-panel');
  const loginCard = document.getElementById('loginCard');
  const alertBanner = document.getElementById('alertBanner');
  const closeAlertBtn = document.getElementById('closeAlertBtn');
  const btnTogglePw = document.getElementById('btnTogglePw');
  const userPasswordInput = document.getElementById('userPassword');
  const btnToggleTheme = document.getElementById('btnToggleTheme');
  const btnToggleAlert = document.getElementById('btnToggleAlert');
  const langToggleBtn = document.getElementById('langToggleBtn');
  const currentLangLabel = document.getElementById('currentLangLabel');
  const welcomeTitle = document.getElementById('welcomeTitle');
  const welcomeSubtitle = document.getElementById('welcomeSubtitle');
  const alertMessage = document.getElementById('alertMessage');

  // Language Dictionary
  let currentLang = 'vi';
  const translations = {
    vi: {
      langLabel: 'Tiếng Việt',
      welcomeTitle: 'Chào mừng bạn <span>quay trở lại!</span>',
      welcomeSubtitle: 'Sử dụng tài khoản Microsoft 365 công ty để truy cập không gian làm việc của bạn.',
      alertError: 'Không thể kiểm tra phiên đăng nhập. Vui lòng thử lại.'
    },
    en: {
      langLabel: 'English',
      welcomeTitle: 'Welcome <span>Back!</span>',
      welcomeSubtitle: 'Use your company Microsoft 365 account to access your workspace.',
      alertError: 'Unable to verify login session. Please try again.'
    }
  };

  // 1. Background Image Switcher (Proves Typography Contrast on Bright vs Dark Backdrops)
  bgBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetBgId = btn.getAttribute('data-bg');
      
      bgBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      bgLayers.forEach(layer => {
        if (layer.id === targetBgId) {
          layer.classList.add('active');
        } else {
          layer.classList.remove('active');
        }
      });
    });
  });

  // 2. Tab Navigation Switcher
  tabBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetTab = btn.getAttribute('data-tab');

      tabBtns.forEach(b => b.classList.remove('active'));
      btn.classList.add('active');

      tabPanels.forEach(panel => {
        if (panel.id === targetTab) {
          panel.classList.add('active');
        } else {
          panel.classList.remove('active');
        }
      });
    });
  });

  // 3. Password Toggle Visibility
  if (btnTogglePw && userPasswordInput) {
    btnTogglePw.addEventListener('click', () => {
      const isPassword = userPasswordInput.type === 'password';
      userPasswordInput.type = isPassword ? 'text' : 'password';
      btnTogglePw.style.color = isPassword ? '#2563eb' : '#94a3b8';
    });
  }

  // 4. Alert Banner Close Button & Demo Toggle
  if (closeAlertBtn && alertBanner) {
    closeAlertBtn.addEventListener('click', () => {
      alertBanner.classList.add('hidden');
    });
  }

  if (btnToggleAlert && alertBanner) {
    btnToggleAlert.addEventListener('click', () => {
      alertBanner.classList.toggle('hidden');
    });
  }

  // 5. Theme Toggle (Light / Dark Glass Mode)
  if (btnToggleTheme && loginCard) {
    btnToggleTheme.addEventListener('click', () => {
      const currentTheme = loginCard.getAttribute('data-theme') || 'light';
      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      loginCard.setAttribute('data-theme', newTheme);
    });
  }

  // 6. Language Switcher Toggle
  if (langToggleBtn) {
    langToggleBtn.addEventListener('click', () => {
      currentLang = currentLang === 'vi' ? 'en' : 'vi';
      const dict = translations[currentLang];
      
      currentLangLabel.textContent = dict.langLabel;
      welcomeTitle.innerHTML = dict.welcomeTitle;
      welcomeSubtitle.textContent = dict.welcomeSubtitle;
      alertMessage.textContent = dict.alertError;
    });
  }

  // 7. Button Click Action Feedback Simulation
  const primaryBtns = document.querySelectorAll('.btn-ms-sso');
  primaryBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      if (btn.classList.contains('loading')) return;
      
      const originalText = btn.innerHTML;
      btn.classList.add('loading');
      btn.innerHTML = `<span style="display:inline-block; animation: spin 1s infinite linear;">⌛</span> Đang kết nối xác thực...`;
      
      setTimeout(() => {
        btn.classList.remove('loading');
        btn.innerHTML = originalText;
        alertBanner.classList.remove('hidden');
      }, 1500);
    });
  });
});
