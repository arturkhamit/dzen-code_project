export async function captchaToken(siteKey) {
  let timeout;
  try {
    // Request a new single-use token for every submission, never for previews.
    const token = await Promise.race([
      new Promise((resolve, reject) => {
        if (!siteKey || !window.grecaptcha?.ready) { reject(new Error('reCAPTCHA is unavailable.')); return; }
        window.grecaptcha.ready(() => {
          Promise.resolve()
            .then(() => window.grecaptcha.execute(siteKey, { action: 'comment_create' }))
            .then(resolve, reject);
        });
      }),
      new Promise((_, reject) => {
        timeout = setTimeout(() => reject(new Error('reCAPTCHA timed out.')), 10000);
      }),
    ]);
    if (typeof token !== 'string' || !token) throw new Error('reCAPTCHA returned no token.');
    return token;
  } finally { clearTimeout(timeout); }
}
