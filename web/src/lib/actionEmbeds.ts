/**
 * Serialization helpers for ActionEmbed data
 */

export type ActionEmbedKind =
  | "plan"
  | "tool"
  | "diff"
  | "sendEmail"
  | "schedule"
  | "runScript"
  | string;

export type ActionEmbedStatus =
  | "proposed"
  | "running"
  | "succeeded"
  | "failed"
  | "cancelled";

export interface ActionEmbed {
  id: string;
  kind: ActionEmbedKind;
  title: string;
  summary: string;
  details?: string;
  preview?: string;
  diff?: string;
  status: ActionEmbedStatus;
  controls?: {
    approve?: boolean;
    edit?: boolean;
    decline?: boolean;
  };
}

/**
 * Serialize ActionEmbed to JSON
 */
export function serializeActionEmbed(embed: ActionEmbed): string {
  return JSON.stringify(embed);
}

/**
 * Deserialize ActionEmbed from JSON
 */
export function deserializeActionEmbed(json: string): ActionEmbed {
  return JSON.parse(json);
}

/**
 * Validate ActionEmbed structure
 */
export function validateActionEmbed(embed: any): embed is ActionEmbed {
  return (
    embed &&
    typeof embed.id === "string" &&
    typeof embed.kind === "string" &&
    typeof embed.title === "string" &&
    typeof embed.summary === "string" &&
    typeof embed.status === "string" &&
    [
      "proposed",
      "running",
      "succeeded",
      "failed",
      "cancelled",
    ].includes(embed.status)
  );
}

