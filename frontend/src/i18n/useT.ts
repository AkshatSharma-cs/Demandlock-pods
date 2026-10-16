import en from "./en.json";
import hi from "./hi.json";
import ta from "./ta.json";
type Keys = keyof typeof en;
const dictionaries = { en, hi, ta };
export function useT() {
  const lang = (localStorage.getItem("lang") || "en") as keyof typeof dictionaries;
  return (key: Keys) => dictionaries[lang]?.[key] ?? en[key];
}
