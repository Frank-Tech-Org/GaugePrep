// WHY: runs in <head> before first paint so the stored theme and language never flash.
// Mirrors parseThemeChoice and detectLocale; boot-script.test.ts keeps them in step.
export const BOOT_SCRIPT = `(function(){var d=document.documentElement;function g(k){try{return localStorage.getItem(k)}catch(e){return null}}var t=g("gp.theme");if(t==="light"||t==="dark")d.setAttribute("data-theme",t);var l=g("gp.locale");if(l!=="fr"&&l!=="en"){var n=(navigator.languages&&navigator.languages[0])||navigator.language||"";l=/^fr(-|_|$)/i.test(n)?"fr":"en"}d.lang=l})()`;
