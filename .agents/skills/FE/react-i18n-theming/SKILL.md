---
name: react-i18n-theming
description: "Bilingual (VI/EN) internationalization and Dark/Light mode theming guidelines for React 18 + Vite + TypeScript. Use when maintaining LanguageContext, ThemeContext, CSS variables/tokens, adding new UI components with localized text, switching between light and dark themes, ensuring WCAG 2.1 AA color contrast, or preventing theme flicker on page reload."
---

# React Bilingual i18n & Dark/Light Theming (Project CDTN2)

Guidelines for managing bilingual internationalization (Vietnamese & English) and Dark/Light mode theme tokens in the **Frontend** (`frontend/src`).

## 1. Bilingual Architecture (`LanguageContext`)

The application supports dual languages: Vietnamese (`vi` - default) and English (`en`).

### 1.1 Context Structure
Located in `frontend/src/context/LanguageContext.tsx`:
- Provides `language` ('vi' | 'en') and `setLanguage(lang)` function.
- Synchronizes with `localStorage.getItem('app_language')`.
- Provides helper function `t(key: string, params?: Record<string, string>): string`.

### 1.2 Localization Rules
1. **Never hardcode raw strings in components**:
   - Always extract text to translation dictionaries (`src/locales/vi.json` and `src/locales/en.json` or typed dictionaries).
   - Example:
     ```tsx
     // ❌ BAD:
     <button>Nộp hồ sơ</button>

     //  GOOD:
     const { t } = useLanguage();
     <button>{t('job.apply_button')}</button>
     ```
2. **Key Naming Convention**:
   - Use dot-notation grouped by domain/feature:
     - `common.save`, `common.cancel`, `common.loading`, `common.error`
     - `auth.login_title`, `auth.email_placeholder`, `auth.password_error`
     - `job.list_title`, `job.budget_range`, `job.apply_now`
     - `nav.home`, `nav.jobs`, `nav.profile`, `nav.admin`
3. **Completeness Check**:
   - Every key present in `vi` must have an exact corresponding key in `en`.

---

## 2. Dark / Light Theme Architecture (`ThemeContext`)

The UI relies on pure CSS design tokens and CSS custom properties without bulky UI frameworks.

### 2.1 Context Implementation
Located in `frontend/src/context/ThemeContext.tsx`:
- Tracks current theme: `'light' | 'dark'`.
- Persists theme in `localStorage.getItem('app_theme')` (defaults to system preference via `window.matchMedia('(prefers-color-scheme: dark)')`).
- Updates `data-theme` attribute on root element:
  ```ts
  document.documentElement.setAttribute('data-theme', theme);
  ```

### 2.2 CSS Design Tokens (`src/styles/variables.css`)
All colors, borders, and shadows must reference semantic CSS variables:

```css
:root {
  /* Light Mode Tokens */
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-card: #ffffff;
  --text-primary: #0f172a;
  --text-secondary: #475569;
  --text-muted: #94a3b8;
  --border-color: #e2e8f0;
  --primary-color: #2563eb;
  --primary-hover: #1d4ed8;
  --success-color: #16a34a;
  --warning-color: #f59e0b;
  --danger-color: #dc2626;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}

[data-theme='dark'] {
  /* Dark Mode Tokens */
  --bg-primary: #0b0f19;
  --bg-secondary: #111827;
  --bg-card: #1f2937;
  --text-primary: #f9fafb;
  --text-secondary: #cbd5e1;
  --text-muted: #64748b;
  --border-color: #374151;
  --primary-color: #3b82f6;
  --primary-hover: #60a5fa;
  --success-color: #22c55e;
  --warning-color: #fbbf24;
  --danger-color: #ef4444;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.5);
}
```

---

## 3. WCAG 2.1 AA Accessibility Standards

1. **Color Contrast Ratio**:
   - Normal text: Minimum 4.5:1 contrast against background.
   - Large text (18pt+ or 14pt bold): Minimum 3:1 contrast.
   - Interactive elements (borders, button focus rings): Minimum 3:1 contrast.
2. **Theme Toggle Component**:
   - Provide clear `aria-label`: `aria-label={theme === 'dark' ? 'Chuyển sang chế độ sáng' : 'Chuyển sang chế độ tối'}`.
   - Include keyboard focus rings: `outline: 2px solid var(--primary-color)`.

---

## 4. Preventing Theme Flicker on Page Load

In `index.html`, execute a tiny inline script before the bundle loads:
```html
<script>
  (function() {
    const saved = localStorage.getItem('app_theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = saved || (prefersDark ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', theme);
  })();
</script>
```
