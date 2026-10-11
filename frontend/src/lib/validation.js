// HTML patterns use Unicode sets, where a literal dash must be escaped.
export const usernamePattern = String.raw`[A-Za-z0-9_\-]+`;

export const formatHints = {
  username: 'Use 1–80 Latin letters (A–Z, a–z), digits (0–9), underscores (_) or dashes (-), with no spaces. Example: Alex_123-test.',
  email: 'Enter an email address, for example alex@example.com.',
  homepage: 'Enter a full URL starting with http:// or https://, for example https://example.com, or leave it empty.',
};

export function updateFieldError(event, errors) {
  const input = event.target;
  // Clear previous custom validity before checking the browser's constraints.
  input.setCustomValidity('');
  if (event.type !== 'invalid' && !errors[input.name]) return;
  const hint = input.name === 'username' && !input.pattern ? '' : formatHints[input.name];
  const message = input.validity.valid ? '' : input.validity.valueMissing
    ? `This field is required.${hint ? ` ${hint}` : ''}`
    : hint || input.validationMessage;
  errors[input.name] = message ? [message] : [];
  input.setCustomValidity(message);
}
