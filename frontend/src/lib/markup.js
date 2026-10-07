import { linkUrl } from "./urls.js";

const allowedTags = { a: ["href", "title"], code: [], i: [], strong: [] };

export const escapeMarkup = (value) => value.replace(/[&<>"']/g, (char) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
})[char]);

export const parseMarkup = (value) => {
  if (!value.trim() || value.length > 10000) throw new Error("Enter between 1 and 10,000 characters.");
  if (value.includes("<!") || value.includes("<?")) throw new Error("Declarations and HTML comments are not allowed.");
  const xml = new DOMParser().parseFromString(`<comment>${value}</comment>`, "application/xml");
  if (xml.querySelector("parsererror")) {
    throw new Error("Close every tag and escape literal & and < characters as &amp; and &lt;.");
  }
  // Rebuild only permitted elements. Never insert a draft with innerHTML.
  // The server validators run the same checks; browser validation is only early feedback.
  const copy = (node, insideLink = false, depth = 0) => {
    if (node.nodeType === Node.TEXT_NODE) return document.createTextNode(node.textContent);
    if (node.nodeType !== Node.ELEMENT_NODE || node.namespaceURI ||
        !Object.hasOwn(allowedTags, node.tagName) || depth > 32) {
      throw new Error("Only a, code, i and strong tags are allowed, up to 32 formatting levels.");
    }
    const tag = node.tagName;
    if (tag === "a" && insideLink) throw new Error("Links cannot contain other links.");
    const element = document.createElement(tag);
    for (const attr of node.attributes) {
      if (!allowedTags[tag].includes(attr.name)) throw new Error(`The ${attr.name} attribute is not allowed.`);
      element.setAttribute(attr.name, attr.value);
    }
    if (tag === "a") {
      linkUrl(node.getAttribute("href") || "");
      element.setAttribute("rel", "nofollow ugc noopener noreferrer");
    }
    for (const child of node.childNodes) element.append(copy(child, insideLink || tag === "a", depth + 1));
    return element;
  };
  const fragment = document.createDocumentFragment();
  for (const child of xml.documentElement.childNodes) fragment.append(copy(child, false, 1));
  if (!fragment.textContent.trim()) throw new Error("Enter a comment containing text.");
  const container = document.createElement("div");
  container.append(fragment);
  return container.innerHTML;
};
