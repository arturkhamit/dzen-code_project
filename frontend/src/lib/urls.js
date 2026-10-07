export const safeUrl = (value, sameOrigin = true) => {
  const url = new URL(value, window.location.href);
  if (!["http:", "https:"].includes(url.protocol) || (sameOrigin && url.origin !== location.origin)) {
    throw new Error("The address is not supported.");
  }
  return url;
};

export const linkUrl = (value) => {
  if (!/^https?:\/\//i.test(value) || /[\s\u0000-\u001f]/u.test(value)) {
    throw new Error("Use a complete http:// or https:// link without spaces.");
  }
  return safeUrl(value, false);
};
