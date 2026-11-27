export type Messages = Readonly<Record<string, string>>;
export type Params = Readonly<Record<string, string | number>>;

/** Looks up `key` and fills `{name}` placeholders. A missing key returns the key itself. */
export function translate(
  messages: Messages,
  key: string,
  params?: Params,
): string {
  const template = messages[key];
  if (template === undefined) return key;
  if (!params) return template;
  return template.replace(/\{(\w+)\}/g, (placeholder, name: string) =>
    name in params ? String(params[name]) : placeholder,
  );
}
