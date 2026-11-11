export interface EmailMetadata {
  name: string;
  subject: string;
  preheader?: string;
}

export interface EmailSettings {
  width: number;
  background_color: string;
  content_background: string;
}

export interface EmailSection {
  id: string;
  type: string;
  props: any;
}

export interface EmailDocument {
  schema_version: number;
  metadata: EmailMetadata;
  settings: EmailSettings;
  sections: EmailSection[];
}

export interface BlockType {
  id: string;
  name: string;
  icon: string;
  category: string;
  description: string;
}