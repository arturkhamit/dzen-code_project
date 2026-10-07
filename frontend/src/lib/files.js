const MAX_TEXT_BYTES = 100 * 1024;
const MAX_IMAGE_BYTES = 10 * 1024 * 1024;

export const decodeText = (bytes) => {
  let value;
  try { value = new TextDecoder("utf-8", { fatal: true }).decode(bytes); }
  catch { throw new Error("Save the TXT file using UTF-8 encoding."); }
  if (/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/u.test(value)) throw new Error("TXT files cannot contain binary data.");
  return value;
};

export const validateFile = async (file) => {
  if (!file) return;
  const extension = file.name.split(".").pop().toLowerCase();
  if (!["jpg", "jpeg", "gif", "png", "txt"].includes(extension)) throw new Error("Choose a JPG, GIF, PNG or TXT file.");
  if (!file.size) throw new Error("The attachment is empty.");
  if (file.size > (extension === "txt" ? MAX_TEXT_BYTES : MAX_IMAGE_BYTES)) {
    throw new Error(extension === "txt" ? "TXT files must be at most 100 KB." : "Images must be at most 10 MB.");
  }
  if (extension === "txt") {
    decodeText(await file.arrayBuffer());
    return;
  }
  const bytes = new Uint8Array(await file.slice(0, 12).arrayBuffer());
  const matches = extension === "png" ? [137, 80, 78, 71, 13, 10, 26, 10].every((n, i) => bytes[i] === n)
    : extension === "gif" ? /^GIF8[79]a/.test(String.fromCharCode(...bytes))
    : bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255;
  if (!matches) throw new Error("The image contents do not match its extension.");
  // Keep the original GIF for the server to resize every frame without losing
  // animation. The attachment service decodes/re-encodes all images before storage.
};

export const readRemoteText = async (response) => {
  if (!response.ok || !response.body) throw new Error("The attachment could not be opened.");
  const reader = response.body.getReader();
  const chunks = [];
  let total = 0;
  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      total += value.length;
      if (total > MAX_TEXT_BYTES) throw new Error("TXT files must be at most 100 KB.");
      chunks.push(value);
    }
  } finally { await reader.cancel(); }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.length; }
  return decodeText(bytes);
};
