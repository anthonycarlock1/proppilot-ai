import { useRef, useState } from "react";
import { Check, LoaderCircle, RefreshCw, Ticket } from "lucide-react";
import {
  confirmTicket,
  updateTicket,
  type TicketDraft,
  type MaintenanceTicket,
} from "./api";

export function TicketConfirmation({
  draft,
  onSaved,
}: {
  draft: TicketDraft;
  onSaved: (ticket: MaintenanceTicket) => void;
}) {
  const [expanded, setExpanded] = useState(false);
  const [property, setProperty] = useState("");
  const [unit, setUnit] = useState("");
  const [reviewed, setReviewed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState<MaintenanceTicket | null>(null);
  const key = useRef(crypto.randomUUID());
  const attempted = useRef<Parameters<typeof confirmTicket>[0] | null>(null);
  const locked = useRef(false);

  async function save() {
    if (!reviewed || property.trim().length < 2 || locked.current) return;
    locked.current = true;
    attempted.current ??= {
      assessment_id: draft.assessment_id,
      property_label: property.trim(),
      unit: unit.trim(),
      confirm_reviewed: true,
    };
    setBusy(true);
    setError("");
    try {
      const result = await confirmTicket(attempted.current, key.current);
      setSaved(result.ticket);
      onSaved(result.ticket);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Ticket could not be saved. Retry this confirmation.",
      );
    } finally {
      setBusy(false);
      locked.current = false;
    }
  }

  if (saved)
    return (
      <div className="ticket-saved" role="status">
        <Check size={15} />
        <div>
          <strong>Ticket saved</strong>
          <span>{saved.ticket_id}</span>
          <small>View it in Tickets. The assessment has been preserved.</small>
        </div>
      </div>
    );
  if (!expanded)
    return (
      <button
        className="review-ticket-button"
        onClick={() => setExpanded(true)}
      >
        <Ticket size={14} />
        Review & create ticket
      </button>
    );
  return (
    <form
      className="ticket-confirmation"
      aria-label="Confirm maintenance ticket"
      onSubmit={(event) => {
        event.preventDefault();
        void save();
      }}
    >
      <h4>Review before creating a ticket</h4>
      <p className="ticket-description">{draft.description}</p>
      <div className="confirmation-facts">
        <span>Category: {draft.assessment.category.toUpperCase()}</span>
        <span>Model urgency: {draft.assessment.urgency}</span>
        <span>
          Recommended priority: {draft.assessment.recommended_priority}
        </span>
      </div>
      <label>
        Property name
        <input
          required
          minLength={2}
          maxLength={120}
          value={property}
          disabled={busy || !!attempted.current}
          onChange={(event) => setProperty(event.target.value)}
          placeholder="e.g. Demo House"
        />
      </label>
      <label>
        Unit (optional)
        <input
          maxLength={40}
          value={unit}
          disabled={busy || !!attempted.current}
          onChange={(event) => setUnit(event.target.value)}
          placeholder="e.g. Unit 2B"
        />
      </label>
      <label className="review-check">
        <input
          type="checkbox"
          checked={reviewed}
          disabled={busy || !!attempted.current}
          onChange={(event) => setReviewed(event.target.checked)}
        />
        I reviewed the issue and AI assessment, and confirm this ticket should
        be created.
      </label>
      {error && (
        <div className="error-message" role="alert">
          {error} Retry uses these same details. You can also refresh the ticket
          list to check whether it was saved.
        </div>
      )}
      <div className="confirmation-actions">
        <button
          type="button"
          className="text-button"
          disabled={busy}
          onClick={() => setExpanded(false)}
        >
          Cancel
        </button>
        <button
          type="submit"
          className="primary-button"
          disabled={busy || !reviewed || property.trim().length < 2}
        >
          {busy ? (
            <LoaderCircle size={14} className="spin" />
          ) : (
            <Check size={14} />
          )}
          Confirm & create ticket
        </button>
      </div>
    </form>
  );
}

export function TicketPanel({
  tickets,
  error,
  loading,
  nextCursor,
  onRefresh,
  onMore,
  onUpdated,
}: {
  tickets: MaintenanceTicket[];
  error: string;
  loading: boolean;
  nextCursor: string | null;
  onRefresh: () => void;
  onMore: () => void;
  onUpdated: (ticket: MaintenanceTicket) => void;
}) {
  const [updating, setUpdating] = useState<string | null>(null);
  const [updateError, setUpdateError] = useState("");
  async function advance(ticket: MaintenanceTicket) {
    if (updating) return;
    setUpdating(ticket.ticket_id);
    setUpdateError("");
    try {
      onUpdated(await updateTicket(ticket));
    } catch (cause) {
      setUpdateError(
        cause instanceof Error
          ? cause.message
          : "Status update failed. Please refresh.",
      );
    } finally {
      setUpdating(null);
    }
  }
  return (
    <section className="panel ticket-panel" aria-label="Maintenance tickets">
      <div className="panel-heading">
        <div>
          <h3>
            <Ticket size={16} />
            Maintenance tickets{" "}
            <span className="count-badge">{tickets.length}</span>
          </h3>
          <p>
            Saved to your shared demo workspace. Use fictional property data.
          </p>
        </div>
        <button className="text-button" disabled={loading} onClick={onRefresh}>
          <RefreshCw size={13} className={loading ? "spin" : ""} />
          Refresh tickets
        </button>
      </div>
      {(error || updateError) && (
        <div className="error-message ticket-panel-error" role="alert">
          {updateError || error}
        </div>
      )}
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>Ticket & property</th>
              <th>Issue</th>
              <th>Priority</th>
              <th>Status</th>
              <th>Next step</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.ticket_id}>
                <td>
                  <div className="ticket-identifier">{ticket.ticket_id}</div>
                  <strong>{ticket.property_label}</strong>
                  <small className="ticket-unit">
                    {ticket.unit || "No unit specified"}
                  </small>
                </td>
                <td>
                  <details className="ticket-issue">
                    <summary>{ticket.description}</summary>
                    <p>
                      Category: {ticket.assessment.category} · Model urgency:{" "}
                      {ticket.assessment.urgency}
                    </p>
                    <p>
                      Models: {ticket.assessment.category_model_version} /{" "}
                      {ticket.assessment.urgency_model_version} · Policy:{" "}
                      {ticket.assessment.policy_version}
                    </p>
                    <p>
                      Review confirmed at creation. Created{" "}
                      {new Date(ticket.created_at).toLocaleString()}.
                    </p>
                    {ticket.assessment.escalation_reasons.map((reason) => (
                      <p key={reason}>{reason.replaceAll("_", " ")}</p>
                    ))}
                  </details>
                </td>
                <td>
                  <span
                    className={`priority-badge ${ticket.assessment.recommended_priority}`}
                  >
                    {ticket.assessment.recommended_priority}
                  </span>
                </td>
                <td>
                  <span className={`ticket-status ${ticket.status}`}>
                    {ticket.status.replace("_", " ")}
                  </span>
                </td>
                <td>
                  {ticket.status !== "resolved" ? (
                    <button
                      className="ticket-action"
                      disabled={!!updating}
                      onClick={() => void advance(ticket)}
                    >
                      {updating === ticket.ticket_id
                        ? "Saving…"
                        : ticket.status === "open"
                          ? "Start work"
                          : "Resolve ticket"}
                    </button>
                  ) : (
                    <span className="resolved-label">
                      <Check size={12} />
                      Resolved
                    </span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {!tickets.length && !loading && !error && (
        <div className="empty-state">
          <Ticket size={27} />
          <h4>No saved tickets yet</h4>
          <p>
            Assess an issue, then review and confirm its ticket in the
            assistant.
          </p>
        </div>
      )}
      {loading && (
        <div className="ticket-loading" role="status">
          Loading saved tickets…
        </div>
      )}
      {nextCursor && (
        <button
          className="ticket-load-more text-button"
          disabled={loading}
          onClick={onMore}
        >
          Load more tickets
        </button>
      )}
      <div className="panel-footer">
        Saved tickets · Open → In progress → Resolved
      </div>
    </section>
  );
}
