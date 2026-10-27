import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ArrowRight,
  ArrowUpRight,
  Check,
  ChevronDown,
  ChevronRight,
  CircleHelp,
  ClipboardList,
  Clock3,
  House,
  LayoutDashboard,
  LoaderCircle,
  Menu,
  MessageSquare,
  Plus,
  Search,
  ShieldCheck,
  Sparkles,
  Ticket,
  Wrench,
  X,
  Zap,
} from "lucide-react";
import {
  sendMessage,
  loadTickets,
  type MaintenanceTicket,
  type Category,
  type Hazard,
  type ChatResponse,
} from "./api";
import "./styles.css";
import { TicketConfirmation, TicketPanel } from "./Tickets";

type Entry = {
  id: number;
  text: string;
  response: ChatResponse;
  created: Date;
};
type Message = {
  id: number;
  role: "user" | "assistant";
  text: string;
  response?: ChatResponse;
};
const labels: Record<Category, string> = {
  hvac: "HVAC",
  plumbing: "Plumbing",
  electrical: "Electrical",
  general: "General",
};
const examples = [
  {
    label: "AC not cooling",
    text: "My tenant says the air conditioner has stopped cooling and the house is very hot. What should I do?",
    icon: House,
  },
  {
    label: "Leaking faucet",
    text: "The kitchen faucet keeps dripping after I close it. What should I do?",
    icon: Wrench,
  },
  {
    label: "Flickering lights",
    text: "The hallway lights flicker when switched on. What should I do?",
    icon: Zap,
  },
];

const hazardLabels: Record<Hazard, string> = {
  fire_or_smoke: "Active fire or smoke",
  gas_odor: "Gas odor",
  active_flooding: "Active flooding",
  sparking_or_live_wiring: "Sparking or exposed live wiring",
  structural_collapse: "Structural collapse",
  carbon_monoxide_alarm: "Carbon monoxide alarm",
};
function App() {
  const [tickets, setTickets] = useState<MaintenanceTicket[]>([]);
  const [ticketError, setTicketError] = useState("");
  const [ticketsLoading, setTicketsLoading] = useState(false);
  const [ticketsLoaded, setTicketsLoaded] = useState(false);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const ticketLoadLock = useRef(false);
  async function refreshTickets(cursor?: string) {
    if (ticketLoadLock.current) return;
    ticketLoadLock.current = true;
    setTicketsLoading(true);
    setTicketError("");
    try {
      const page = await loadTickets(cursor);
      setTickets((previous) =>
        cursor
          ? [
              ...new Map(
                [...previous, ...page.items].map((ticket) => [
                  ticket.ticket_id,
                  ticket,
                ]),
              ).values(),
            ]
          : page.items,
      );
      setNextCursor(page.next_cursor);
      setTicketsLoaded(true);
    } catch (cause) {
      setTicketError(
        cause instanceof Error ? cause.message : "Unable to load tickets.",
      );
    } finally {
      ticketLoadLock.current = false;
      setTicketsLoading(false);
    }
  }
  function ticketChanged(ticket: MaintenanceTicket) {
    setTickets((previous) =>
      [
        ticket,
        ...previous.filter((item) => item.ticket_id !== ticket.ticket_id),
      ].sort((a, b) => b.ticket_id.localeCompare(a.ticket_id)),
    );
    setTicketsLoaded(true);
  }
  useEffect(() => {
    void refreshTickets();
  }, []);
  const [entries, setEntries] = useState<Entry[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [draft, setDraft] = useState("");
  const [hazards, setHazards] = useState<Hazard[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [chatOpen, setChatOpen] = useState(false);
  const [mobileNav, setMobileNav] = useState(false);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState("all");
  const [section, setSection] = useState("Dashboard");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const requestLock = useRef(false);
  const [notice, setNotice] = useState(false);
  const classified = entries.filter(
    (entry) => entry.response.tool_results.length,
  );
  const categoryCount = new Set(
    classified.map((entry) => entry.response.tool_results[0].result.category),
  ).size;
  const counts = Object.fromEntries(
    Object.keys(labels).map((key) => [
      key,
      classified.filter(
        (e) => e.response.tool_results[0].result.category === key,
      ).length,
    ]),
  ) as Record<Category, number>;
  const visibleEntries = entries.filter(
    (entry) =>
      entry.text.toLowerCase().includes(search.toLowerCase()) &&
      (filter === "all" ||
        entry.response.tool_results[0]?.result.category === filter),
  );

  useEffect(() => {
    chatRef.current?.scrollTo({
      top: chatRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, busy, error]);
  useEffect(() => {
    if (!chatOpen && !notice) return;
    const previous = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = previous;
    };
  }, [chatOpen, notice]);
  useEffect(() => {
    if (!chatOpen) return;
    inputRef.current?.focus();
    const handleKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setChatOpen(false);
        triggerRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [chatOpen]);

  function openChat(text = "") {
    if (text) setDraft(text);
    setChatOpen(true);
    setMobileNav(false);
  }
  async function submit() {
    const text = draft.trim();
    if (text.length < 3 || requestLock.current) return;
    requestLock.current = true;
    setBusy(true);
    setError("");
    setDraft("");
    setMessages((previous) => [
      ...previous,
      { id: Date.now(), role: "user", text },
    ]);
    try {
      const response = await sendMessage(text, hazards);
      setHazards([]);
      const id = Date.now();
      setMessages((previous) => [
        ...previous,
        { id, role: "assistant", text: response.reply.trim(), response },
      ]);
      setEntries((previous) => [
        { id, text, response, created: new Date() },
        ...previous,
      ]);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Something went wrong. Please try again.",
      );
      setDraft(text);
    } finally {
      setBusy(false);
      requestLock.current = false;
    }
  }

  return (
    <div className="app-shell">
      {mobileNav && (
        <button
          className="nav-backdrop"
          aria-label="Close navigation"
          onClick={() => setMobileNav(false)}
        />
      )}
      <aside className={`sidebar ${mobileNav ? "nav-open" : ""}`}>
        <a
          className="brand"
          href="#"
          onClick={(event) => {
            event.preventDefault();
            setSection("Dashboard");
            setMobileNav(false);
          }}
        >
          <span className="brand-mark">
            <House size={21} strokeWidth={2.4} />
          </span>
          PropPilot <b>AI</b>
        </a>
        <div className="workspace-switch">
          <span className="workspace-avatar">P</span>
          <div>
            My workspace<small>Property management</small>
          </div>
          <ChevronDown size={15} />
        </div>
        <p className="nav-label">WORKSPACE</p>
        <nav aria-label="Main navigation">
          {[
            { name: "Dashboard", icon: LayoutDashboard },
            { name: "Request activity", icon: ClipboardList },
          ].map(({ name, icon: Icon }) => (
            <button
              key={name}
              className={`nav-item ${section === name ? "selected" : ""}`}
              onClick={() => {
                setSection(name);
                setMobileNav(false);
                document
                  .getElementById("activity")
                  ?.scrollIntoView({ behavior: "smooth", block: "center" });
              }}
            >
              <Icon size={18} />
              {name}
              {name === "Request activity" && entries.length > 0 && (
                <span className="nav-count">{entries.length}</span>
              )}
            </button>
          ))}
          <button className="nav-item" onClick={() => openChat()}>
            <Sparkles size={18} />
            AI assistant<span className="tiny-pill">NEW</span>
          </button>
          <button
            className={`nav-item ${section === "Tickets" ? "selected" : ""}`}
            onClick={() => {
              setSection("Tickets");
              setMobileNav(false);
            }}
          >
            <Ticket size={18} />
            Tickets
            <span className="nav-count">
              {ticketsLoaded ? tickets.length : "—"}
            </span>
          </button>
        </nav>
        <div className="sidebar-bottom">
          <div className="sidebar-callout">
            <div className="callout-icon">
              <Sparkles size={19} />
            </div>
            <strong>A little help. A lot less busywork.</strong>
            <p>Let AI help you find the right next step.</p>
            <button onClick={() => openChat()}>
              Ask PropPilot <ArrowUpRight size={15} />
            </button>
          </div>
          <button
            className="nav-item help-item"
            onClick={() => setNotice(true)}
          >
            <CircleHelp size={18} />
            About this workspace
          </button>
          <div className="profile">
            <span className="avatar">AC</span>
            <div>
              Anthony Carlock<small>Workspace owner</small>
            </div>
            <ShieldCheck size={16} />
          </div>
        </div>
      </aside>

      <main className="workspace">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon-button mobile-menu"
              aria-label="Open navigation"
              onClick={() => setMobileNav(true)}
            >
              <Menu size={20} />
            </button>
            <House size={16} />
            <ChevronRight size={14} />
            <span>{section}</span>
          </div>
          <div className="topbar-right">
            <span className="workspace-tag">
              <span />
              Development workspace
            </span>
            <button
              className="icon-button"
              aria-label="About this workspace"
              onClick={() => setNotice(true)}
            >
              <CircleHelp size={19} />
            </button>
            <span className="avatar small">AC</span>
          </div>
        </header>
        <section className="hero">
          <div className="hero-copy">
            <span className="eyebrow">A CLEARER VIEW OF MAINTENANCE</span>
            <h1>
              Welcome back, Anthony<span>.</span>
            </h1>
            <p>
              A little less managing.
              <br />A little more peace of mind.
            </p>
          </div>
          <div className="hero-caption">
            <House size={13} />
            Built for the places people call home
          </div>
        </section>
        <div className="page-content">
          <div className="page-heading">
            <div>
              <h2>Your maintenance overview</h2>
              <p>From the first message to the right next step.</p>
            </div>
            <button
              ref={triggerRef}
              className="primary-button"
              onClick={() => openChat()}
            >
              <Plus size={17} />
              New request
            </button>
          </div>
          <section className="stats" aria-label="Session overview">
            {[
              {
                label: "Requests analyzed",
                value: entries.length,
                note: "In this browser session",
                icon: ClipboardList,
                color: "blue",
              },
              {
                label: "Categories identified",
                value: categoryCount,
                note: "Across 4 maintenance categories",
                icon: House,
                color: "purple",
              },
              {
                label: "Needs clarification",
                value: entries.length - classified.length,
                note: "Requests without a classification",
                icon: MessageSquare,
                color: "amber",
              },
              {
                label: "Active tickets",
                value: ticketsLoaded
                  ? tickets.filter((ticket) => ticket.status !== "resolved")
                      .length
                  : "—",
                note: ticketError
                  ? "Ticket data unavailable · refresh"
                  : "Across loaded saved tickets",
                icon: Ticket,
                color: "gray",
              },
            ].map(({ label, value, note, icon: Icon, color }) => (
              <article className="stat-card" key={label}>
                <div className="stat-top">
                  <span>{label}</span>
                  <span className={`stat-icon ${color}`}>
                    <Icon size={17} />
                  </span>
                </div>
                <strong>{value}</strong>
                <small>{note}</small>
              </article>
            ))}
          </section>
          <section className="quick-start">
            <div className="quick-copy">
              <span className="sparkle-tile">
                <Sparkles size={20} />
              </span>
              <div>
                <h3>What needs attention today?</h3>
                <p>Describe an issue. We’ll help you make sense of it.</p>
              </div>
            </div>
            <div className="example-buttons">
              {examples.map(({ label, text, icon: Icon }) => (
                <button key={label} onClick={() => openChat(text)}>
                  <Icon size={15} />
                  {label}
                  <ArrowUpRight size={14} />
                </button>
              ))}
            </div>
          </section>
          {section === "Tickets" && (
            <TicketPanel
              tickets={tickets}
              error={ticketError}
              loading={ticketsLoading}
              nextCursor={nextCursor}
              onRefresh={() => void refreshTickets()}
              onMore={() => void refreshTickets(nextCursor || undefined)}
              onUpdated={ticketChanged}
            />
          )}
          <div className="dashboard-grid" hidden={section === "Tickets"}>
            <section className="panel activity-panel" id="activity">
              <div className="panel-heading">
                <div>
                  <h3>
                    Recent request activity{" "}
                    <span className="count-badge">{entries.length}</span>
                  </h3>
                  <p>Your conversations, organized at a glance.</p>
                </div>
                <span className="session-label">
                  <Clock3 size={13} />
                  This session
                </span>
              </div>
              <div className="table-toolbar">
                <label className="search-field">
                  <Search size={16} />
                  <input
                    aria-label="Search requests"
                    placeholder="Search requests…"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </label>
                <select
                  aria-label="Filter by category"
                  value={filter}
                  onChange={(event) => setFilter(event.target.value)}
                >
                  <option value="all">All categories</option>
                  {Object.entries(labels).map(([key, label]) => (
                    <option key={key} value={key}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>
              <div className="table-scroll">
                <table>
                  <thead>
                    <tr>
                      <th>Maintenance request</th>
                      <th>Category</th>
                      <th>Recommended priority</th>
                      <th>Time</th>
                    </tr>
                  </thead>
                  <tbody>
                    {visibleEntries.map((entry) => {
                      const prediction = entry.response.tool_results[0]?.result;
                      return (
                        <tr key={entry.id}>
                          <td>
                            <div className="request-cell">
                              <span className="request-icon">
                                <ClipboardList size={16} />
                              </span>
                              <div>
                                <span title={entry.text}>{entry.text}</span>
                                <small>
                                  Session request ·{" "}
                                  {String(
                                    entries.length - entries.indexOf(entry),
                                  ).padStart(3, "0")}
                                </small>
                              </div>
                            </div>
                          </td>
                          <td>
                            {prediction ? (
                              <span
                                className={`category-badge ${prediction.category}`}
                              >
                                {labels[prediction.category]}
                              </span>
                            ) : (
                              <span className="category-badge general">
                                Unclassified
                              </span>
                            )}
                          </td>
                          <td>
                            {prediction?.urgency_assessment ? (
                              <div className="priority-cell">
                                <span
                                  className={`priority-badge ${prediction.urgency_assessment.recommended_priority}`}
                                >
                                  {
                                    prediction.urgency_assessment
                                      .recommended_priority
                                  }
                                </span>
                                <small>Manual review required</small>
                              </div>
                            ) : (
                              <span className="assessment-status">
                                Not assessed
                              </span>
                            )}
                          </td>
                          <td className="time-cell">
                            {entry.created.toLocaleTimeString([], {
                              hour: "2-digit",
                              minute: "2-digit",
                            })}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
              {visibleEntries.length === 0 && (
                <div className="empty-state">
                  <div className="empty-illustration">
                    <div className="empty-dot dot-one" />
                    <div className="empty-dot dot-two" />
                    <ClipboardList size={31} strokeWidth={1.4} />
                    <span>
                      <Check size={11} />
                    </span>
                  </div>
                  <h4>
                    {entries.length
                      ? "No matching requests"
                      : "Your next step starts here"}
                  </h4>
                  <p>
                    {entries.length
                      ? "Try a different search or category."
                      : "Describe your first maintenance issue and see your AI assessment here."}
                  </p>
                  {!entries.length && (
                    <button className="text-button" onClick={() => openChat()}>
                      Start a request <ArrowRight size={15} />
                    </button>
                  )}
                </div>
              )}
              <div className="panel-footer">
                <ShieldCheck size={14} />
                Session activity only. Save a reviewed assessment as a ticket
                from the assistant.
              </div>
            </section>
            <aside className="panel breakdown-panel">
              <div className="panel-heading">
                <div>
                  <h3>
                    <Sparkles size={16} />
                    AI assessment overview
                  </h3>
                  <p>Understanding your maintenance mix.</p>
                </div>
              </div>
              <div className="donut-area">
                <div
                  className="donut"
                  style={{
                    background: classified.length
                      ? `conic-gradient(#3888fa 0% ${(counts.hvac / classified.length) * 100}%, #79b5fd ${(counts.hvac / classified.length) * 100}% ${((counts.hvac + counts.plumbing) / classified.length) * 100}%, #b5d7ff ${((counts.hvac + counts.plumbing) / classified.length) * 100}% ${((counts.hvac + counts.plumbing + counts.electrical) / classified.length) * 100}%, #dceaff ${((counts.hvac + counts.plumbing + counts.electrical) / classified.length) * 100}% 100%)`
                      : undefined,
                  }}
                >
                  <div>
                    <strong>{classified.length}</strong>
                    <span>classified requests</span>
                  </div>
                </div>
                <p>
                  {classified.length
                    ? "Category distribution this session"
                    : "Your request breakdown will appear here"}
                </p>
              </div>
              <div className="legend">
                {Object.entries(labels).map(([key, label], index) => (
                  <div key={key}>
                    <span className={`legend-dot legend-${index}`} />
                    <span>{label}</span>
                    <strong>{counts[key as Category]}</strong>
                  </div>
                ))}
              </div>
              <div className="advisory">
                <ShieldCheck size={16} />
                <p>
                  AI predictions are advisory.
                  <br />A professional should confirm the issue.
                </p>
              </div>
            </aside>
          </div>
          <section className="workflow-note">
            <span>
              <span className="workflow-mark">
                <Zap size={15} />
              </span>
              <strong>One connected workflow.</strong> Describe it. Classify it.
              Know your next step.
            </span>
            <button className="text-button" onClick={() => openChat()}>
              Meet your assistant <ArrowRight size={15} />
            </button>
          </section>
          <footer className="page-footer">
            <span>
              PropPilot AI <span>·</span> Thoughtful maintenance starts here.
            </span>
            <span>
              Category & urgency available <span>·</span> Durable maintenance
              tickets
            </span>
          </footer>
        </div>
      </main>

      {chatOpen && (
        <div className="chat-layer">
          <button
            className="chat-backdrop"
            aria-label="Close assistant"
            onClick={() => {
              setChatOpen(false);
              triggerRef.current?.focus();
            }}
          />
          <section
            className="chat-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="chat-title"
            onKeyDown={(event) => {
              if (event.key === "Tab") {
                const focusable =
                  event.currentTarget.querySelectorAll<HTMLElement>(
                    "button:not(:disabled), textarea:not(:disabled), input:not(:disabled), summary",
                  );
                const first = focusable[0];
                const last = focusable[focusable.length - 1];
                if (event.shiftKey && document.activeElement === first) {
                  event.preventDefault();
                  last?.focus();
                } else if (!event.shiftKey && document.activeElement === last) {
                  event.preventDefault();
                  first?.focus();
                }
              }
            }}
          >
            <div className="chat-header">
              <span className="assistant-mark">
                <Sparkles size={21} />
              </span>
              <div>
                <h2 id="chat-title">Your maintenance assistant</h2>
                <p>Let’s find the right next step.</p>
              </div>
              <button
                className="icon-button"
                aria-label="Close assistant"
                onClick={() => {
                  setChatOpen(false);
                  triggerRef.current?.focus();
                }}
              >
                <X size={20} />
              </button>
            </div>
            <div className="chat-scope">
              <ShieldCheck size={14} />
              AI assessment · Ticket creation requires your confirmation
            </div>
            <div
              className="chat-messages"
              ref={chatRef}
              aria-live="polite"
              aria-relevant="additions text"
            >
              {messages.length === 0 && (
                <div className="chat-welcome">
                  <span className="welcome-icon">
                    <Sparkles size={29} />
                  </span>
                  <h3>A good place to start.</h3>
                  <p>
                    Tell me what’s happening at your property. I’ll help
                    identify the issue and suggest a next step.
                  </p>
                  <div className="welcome-example">
                    <MessageSquare size={15} />
                    <span>
                      “The AC is running, but the house isn’t cooling down.”
                    </span>
                  </div>
                </div>
              )}
              {messages.map((message) => (
                <article
                  className={`chat-message ${message.role}`}
                  key={message.id}
                >
                  <span className="message-author">
                    {message.role === "user" ? (
                      "You"
                    ) : (
                      <>
                        <Sparkles size={12} />
                        PropPilot AI
                      </>
                    )}
                  </span>
                  <p>{message.text}</p>
                  {message.response?.tool_results.map((tool, index) => (
                    <div className="prediction-detail" key={index}>
                      <span
                        className={`category-badge ${tool.result.category}`}
                      >
                        {labels[tool.result.category]}
                      </span>
                      <span>
                        {tool.result.provider === "sagemaker"
                          ? "Hosted model"
                          : "Local model"}{" "}
                        · v{tool.result.model_version}
                      </span>
                      {tool.result.urgency_assessment && (
                        <div className="urgency-detail">
                          <span
                            className={`priority-badge ${tool.result.urgency_assessment.recommended_priority}`}
                          >
                            Priority:{" "}
                            {
                              tool.result.urgency_assessment
                                .recommended_priority
                            }
                          </span>
                          <span>
                            Model urgency:{" "}
                            {tool.result.urgency_assessment.urgency} ·{" "}
                            {tool.result.urgency_assessment.provider ===
                            "sagemaker"
                              ? "Hosted urgency model"
                              : "Local urgency model"}
                          </span>
                          <strong>Manual review required</strong>
                          {tool.result.urgency_assessment.escalation_reasons.map(
                            (reason) => (
                              <span key={reason}>
                                {reason.replaceAll("_", " ")}
                              </span>
                            ),
                          )}
                        </div>
                      )}
                    </div>
                  ))}
                  {message.response?.ticket_draft && (
                    <TicketConfirmation
                      draft={message.response.ticket_draft}
                      onSaved={ticketChanged}
                    />
                  )}
                  {message.response?.ticket_draft_error && (
                    <div className="error-message">
                      {message.response.ticket_draft_error}
                    </div>
                  )}
                </article>
              ))}
              {busy && (
                <div className="thinking" role="status">
                  <LoaderCircle size={16} className="spin" />
                  Assessing your request…
                </div>
              )}
              {error && (
                <div className="error-message" role="alert">
                  {error} Your description is restored below.
                </div>
              )}
            </div>
            <form
              className="chat-composer"
              onSubmit={(event) => {
                event.preventDefault();
                void submit();
              }}
            >
              <label className="sr-only" htmlFor="maintenance-message">
                Describe the maintenance issue
              </label>
              <details className="hazard-options">
                <summary>Report a confirmed hazard (optional)</summary>
                <p>
                  Select only hazards explicitly reported. An empty list does
                  not mean the property is safe.
                </p>
                {Object.entries(hazardLabels).map(([key, label]) => (
                  <label key={key}>
                    <input
                      type="checkbox"
                      disabled={busy}
                      checked={hazards.includes(key as Hazard)}
                      onChange={(event) =>
                        setHazards((previous) =>
                          event.target.checked
                            ? [...previous, key as Hazard]
                            : previous.filter((value) => value !== key),
                        )
                      }
                    />
                    {label}
                  </label>
                ))}
              </details>
              <textarea
                ref={inputRef}
                id="maintenance-message"
                value={draft}
                maxLength={4000}
                disabled={busy}
                onChange={(event) => setDraft(event.target.value)}
                placeholder="What’s happening at your property?"
                onKeyDown={(event) => {
                  if (
                    event.key === "Enter" &&
                    !event.shiftKey &&
                    !event.nativeEvent.isComposing
                  ) {
                    event.preventDefault();
                    void submit();
                  }
                }}
                rows={3}
              />
              <div className="composer-footer">
                <span>
                  {draft.length}/4000 <span>·</span> Shift + Enter for a new
                  line
                </span>
                <button
                  className="send-button"
                  type="submit"
                  aria-label="Send request"
                  disabled={busy || draft.trim().length < 3}
                >
                  {busy ? (
                    <LoaderCircle size={17} className="spin" />
                  ) : (
                    <ArrowRight size={19} />
                  )}
                </button>
              </div>
              <p className="chat-disclaimer">
                Each request is assessed independently. Activity clears on
                refresh.
              </p>
            </form>
          </section>
        </div>
      )}
      {notice && (
        <div className="notice-layer">
          <section
            role="dialog"
            aria-modal="true"
            aria-labelledby="notice-title"
            className="notice"
          >
            <button
              className="icon-button"
              aria-label="Close information"
              autoFocus
              onClick={() => setNotice(false)}
            >
              <X size={19} />
            </button>
            <Sparkles size={26} />
            <h2 id="notice-title">Built one useful step at a time.</h2>
            <p>
              This development workspace currently classifies maintenance issues
              using Bedrock, LangChain, and two SageMaker models for category
              and urgency. All urgency assessments require manual review.
              Reviewed assessments can be saved as durable tickets. Accounts and contractor workflows remain pending.
            </p>
            <button
              className="primary-button"
              onClick={() => {
                setNotice(false);
                openChat();
              }}
            >
              Try the assistant <ArrowRight size={16} />
            </button>
          </section>
        </div>
      )}
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
