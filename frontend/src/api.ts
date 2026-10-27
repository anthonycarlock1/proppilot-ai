export type Category = "hvac" | "plumbing" | "electrical" | "general";
export type Hazard =
  | "fire_or_smoke"
  | "gas_odor"
  | "active_flooding"
  | "sparking_or_live_wiring"
  | "structural_collapse"
  | "carbon_monoxide_alarm";
export type UrgencyAssessment = {
  urgency: "low" | "medium" | "high" | "emergency";
  recommended_priority: "low" | "medium" | "high" | "emergency";
  probabilities: Record<string, number>;
  provider: "local" | "sagemaker";
  model_version: string;
  policy_version: string;
  confirmed_hazards: Hazard[];
  escalation_reasons: string[];
  manual_review_required: true;
};
export type Prediction = {
  category: Category;
  urgency_assessment?: UrgencyAssessment;
  probabilities: Record<Category, number>;
  provider: "local" | "sagemaker";
  model_version: string;
};
export type StoredAssessment = {
  category: Category;
  category_model_version: string;
  category_provider: string;
  urgency: UrgencyAssessment["urgency"];
  urgency_model_version: string;
  urgency_provider: string;
  recommended_priority: UrgencyAssessment["recommended_priority"];
  policy_version: string;
  confirmed_hazards: Hazard[];
  escalation_reasons: string[];
  manual_review_required: true;
};
export type TicketDraft = {
  assessment_id: string;
  description: string;
  assessment: StoredAssessment;
  expires_at: number;
};
export type MaintenanceTicket = {
  ticket_id: string;
  assessment_id: string;
  description: string;
  property_label: string;
  unit: string;
  assessment: StoredAssessment;
  status: "open" | "in_progress" | "resolved";
  version: number;
  created_at: string;
  updated_at: string;
  confirm_reviewed: true;
};
export type TicketPage = {
  items: MaintenanceTicket[];
  next_cursor: string | null;
};
export type ChatResponse = {
  ticket_draft?: TicketDraft;
  ticket_draft_error?: string;
  reply: string;
  foundation_model: string;
  tool_results: { tool: string; result: Prediction }[];
};

export async function sendMessage(
  message: string,
  confirmedHazards: Hazard[] = [],
): Promise<ChatResponse> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 240_000);
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, confirmed_hazards: confirmedHazards }),
      signal: controller.signal,
    });
    if (!response.ok)
      throw new Error(
        "The assistant could not complete this request. Please try again.",
      );
    const result = await response.json();
    if (
      typeof result.reply !== "string" ||
      !Array.isArray(result.tool_results)
    ) {
      throw new Error(
        "The assistant returned an unexpected response. Please try again.",
      );
    }
    return result;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(
        "This request took too long. Please try again in a moment.",
      );
    }
    if (error instanceof TypeError)
      throw new Error(
        "Unable to reach the assistant. Check your connection and try again.",
      );
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

async function ticketRequest<T>(
  path: string,
  method = "GET",
  payload?: unknown,
  key?: string,
): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 30_000);
  try {
    const response = await fetch("/api" + path, {
      method,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        ...(key ? { "Idempotency-Key": key } : {}),
      },
      ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
    });
    const data = await response.json().catch(() => null);
    if (!response.ok)
      throw new Error(
        typeof data?.detail === "string"
          ? data.detail
          : "Ticket operation failed. Please retry.",
      );
    if (!data) throw new Error("Unexpected ticket response. Please refresh.");
    return data as T;
  } catch (error) {
    if (error instanceof Error && error.name === "AbortError")
      throw new Error(
        "Ticket request timed out. Retry the same confirmation safely.",
      );
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
export function loadTickets(cursor?: string): Promise<TicketPage> {
  return ticketRequest(
    "/tickets?limit=20" +
      (cursor ? "&cursor=" + encodeURIComponent(cursor) : ""),
  );
}
export function confirmTicket(
  payload: {
    assessment_id: string;
    property_label: string;
    unit: string;
    confirm_reviewed: true;
  },
  key: string,
) {
  return ticketRequest<{ ticket: MaintenanceTicket; replayed: boolean }>(
    "/tickets",
    "POST",
    payload,
    key,
  );
}
export function updateTicket(ticket: MaintenanceTicket) {
  return ticketRequest<MaintenanceTicket>(
    "/tickets/" + encodeURIComponent(ticket.ticket_id),
    "PATCH",
    {
      status: ticket.status === "open" ? "in_progress" : "resolved",
      expected_version: ticket.version,
    },
  );
}
