
import zh_cn from './zh_cn';

export interface ILanguageResources {
  [key: string]: string | ILanguageResources;
}

const messages: Record<string, ILanguageResources> = {
  ...zh_cn,
};

export default messages;
