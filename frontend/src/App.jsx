
import { useMemo, useState } from "react";
import {
  Activity,
  ArrowRight,
  ArrowUpRight,
  Bell,
  BookOpen,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronDown,
  CircleHelp,
  ClipboardCheck,
  GraduationCap,
  LayoutDashboard,
  Menu,
  Search,
  Settings as SettingsIcon,
  ShieldCheck,
  Users,
  X,
  UserRound,
  SlidersHorizontal,
  Pencil,
  Trash2,
} from "lucide-react";

const initialDemands = [
  {
    company: "GreenLeaf Organics",
    skill: "Digital Marketing",
    location: "Local area",
    slots: 3,
    status: "Confirmed",
    initials: "GL",
    color: "bg-emerald-100 text-emerald-800",
  },
  {
    company: "Village Tech Services",
    skill: "Computer Basics",
    location: "Local area",
    slots: 4,
    status: "Needs review",
    initials: "VT",
    color: "bg-blue-100 text-blue-800",
  },
  {
    company: "Community Retail Hub",
    skill: "Retail Operations",
    location: "Local area",
    slots: 2,
    status: "Confirmed",
    initials: "CR",
    color: "bg-amber-100 text-amber-800",
  },
  {
    company: "Accenture",
    skill: "Coding",
    location: "Local area",
    slots: 2,
    status: "Needs review",
    initials: "AC",
    color: "bg-violet-100 text-violet-800",
  },
];

const pods = [
  {
    title: "Digital Marketing Basics",
    teacher: "Demo teacher",
    learners: 12,
    progress: 72,
    tag: "In progress",
    color: "bg-emerald-600",
  },
  {
    title: "Computer Fundamentals",
    teacher: "Demo teacher",
    learners: 15,
    progress: 48,
    tag: "In progress",
    color: "bg-blue-600",
  },
  {
    title: "Retail Skills & Communication",
    teacher: "Demo teacher",
    learners: 8,
    progress: 86,
    tag: "Near completion",
    color: "bg-violet-600",
  },
];

const learners = [
  {
    id: "L001",
    name: "Demo Learner A",
    skill: "Digital Marketing",
    pod: "Digital Marketing Basics",
    progress: 80,
  },
  {
    id: "L002",
    name: "Demo Learner B",
    skill: "Computer Basics",
    pod: "Computer Fundamentals",
    progress: 55,
  },
  {
    id: "L003",
    name: "Demo Learner C",
    skill: "Retail Operations",
    pod: "Retail Skills & Communication",
    progress: 90,
  },
  {
    id: "L004",
    name: "Demo Learner D",
    skill: "Computer Basics",
    pod: "Computer Fundamentals",
    progress: 40,
  },
  {
    id: "L005",
    name: "Demo Learner E",
    skill: "Digital Marketing",
    pod: "Digital Marketing Basics",
    progress: 65,
  },
];

const tasks = [
  {
    id: 1,
    name: "Create a sample social media post",
    learner: "Demo Learner A",
    skill: "Digital Marketing",
  },
  {
    id: 2,
    name: "Complete a computer basics exercise",
    learner: "Demo Learner B",
    skill: "Computer Basics",
  },
  {
    id: 3,
    name: "Role-play a customer interaction",
    learner: "Demo Learner C",
    skill: "Retail Operations",
  },
];

const outcomes = [
  {
    title: "Practical task completed",
    value: "24",
    category: "Training",
    status: "Illustrative demo figure",
  },
  {
    title: "Employer review recorded",
    value: "12",
    category: "Employer",
    status: "Illustrative demo figure",
  },
  {
    title: "Trial or interview",
    value: "6",
    category: "Opportunity",
    status: "Illustrative demo figure",
  },
  {
    title: "Verified start or payment",
    value: "2",
    category: "Verified outcomes",
    status: "Illustrative demo figure",
  },
];

const navItems = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Employer Demand", icon: BriefcaseBusiness },
  { label: "Learning Pods", icon: BookOpen },
  { label: "Learners", icon: GraduationCap },
  { label: "Teacher Review", icon: ClipboardCheck },
  { label: "Impact & Outcomes", icon: Activity },
  { label: "Settings", icon: SettingsIcon },
];

function matchesQuery(query, ...values) {
  const q = query.trim().toLowerCase();
  return (
    !q ||
    values.some((value) =>
      String(value ?? "").toLowerCase().includes(q)
    )
  );
}

function SectionTitle({ eyebrow, title, description, action }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <p className="mb-1 text-xs font-bold uppercase tracking-[0.16em] text-emerald-700">
          {eyebrow}
        </p>
        <h2 className="text-xl font-bold tracking-tight text-slate-900">
          {title}
        </h2>
        {description && (
          <p className="mt-1 text-sm text-slate-500">
            {description}
          </p>
        )}
      </div>
      {action}
    </div>
  );
}

function EmptyState({ message = "No matching records found." }) {
  return (
    <div className="rounded-xl border border-dashed border-slate-200 px-5 py-10 text-center">
      <Search className="mx-auto mb-3 text-slate-300" size={25} />
      <p className="text-sm text-slate-500">{message}</p>
    </div>
  );
}

function StatCard({ title, value, subtitle, icon: Icon }) {
  return (
    <article className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm shadow-slate-200/40">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-sm font-medium text-slate-500">{title}</p>
          <p className="mt-3 text-3xl font-bold tracking-tight text-slate-900">
            {value}
          </p>
        </div>
        <div className="rounded-xl bg-emerald-50 p-3 text-emerald-700">
          <Icon size={21} />
        </div>
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-2 text-xs">
        <span className="flex items-center gap-1 font-semibold text-emerald-700">
          <ArrowUpRight size={14} />
          Demo data
        </span>
        <span className="text-slate-400">{subtitle}</span>
      </div>
    </article>
  );
}

function StatusBadge({ status }) {
  const styles = {
    Confirmed: "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
    "Needs review": "bg-amber-50 text-amber-700 ring-amber-600/20",
    "In progress": "bg-blue-50 text-blue-700 ring-blue-600/15",
    "Near completion": "bg-violet-50 text-violet-700 ring-violet-600/15",
    Reviewed: "bg-emerald-50 text-emerald-700 ring-emerald-600/15",
  };

  return (
    <span
      className={`inline-flex whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ring-inset ${
        styles[status] || "bg-slate-100 text-slate-600 ring-slate-200"
      }`}
    >
      {status}
    </span>
  );
}

function Overview({ onNavigate, query, demands }) {
  const filteredDemands = demands.filter((d) =>
    matchesQuery(query, d.company, d.skill, d.status, d.location, d.slots)
  );

  const filteredPods = pods.filter((p) =>
    matchesQuery(query, p.title, p.teacher, p.tag)
  );

  const chart = [
    { day: "Mon", value: 35 },
    { day: "Tue", value: 58 },
    { day: "Wed", value: 43 },
    { day: "Thu", value: 76 },
    { day: "Fri", value: 54 },
    { day: "Sat", value: 88 },
    { day: "Sun", value: 66 },
  ];

  return (
    <>
      <section className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          title="Confirmed job slots"
          value={demands
            .filter((d) => d.status === "Confirmed")
            .reduce((sum, d) => sum + Number(d.slots), 0)}
          subtitle="Sample demand records"
          icon={BriefcaseBusiness}
        />
        <StatCard
          title="Active learning pods"
          value="3"
          subtitle="Sample training cohorts"
          icon={BookOpen}
        />
        <StatCard
          title="Learners enrolled"
          value="35"
          subtitle="Across sample pods"
          icon={Users}
        />
        <StatCard
          title="Tasks completed"
          value="68%"
          subtitle="Illustrative cohort average"
          icon={ClipboardCheck}
        />
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <article className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
          <SectionTitle
            eyebrow="Demand insights"
            title="Local skill activity"
            description="Sample visual for the dashboard prototype"
            action={
              <button
                onClick={() => onNavigate("Employer Demand")}
                className="flex items-center gap-1 text-sm font-semibold text-emerald-700"
              >
                View demand <ArrowRight size={15} />
              </button>
            }
          />
          <p className="text-3xl font-bold text-slate-900">
            {demands.reduce((sum, d) => sum + Number(d.slots), 0)} sample slots
          </p>
          <p className="mt-1 text-sm text-slate-500">
            Across seeded demo records
          </p>

          <div className="mt-6 flex h-44 items-end justify-between gap-3 border-b border-slate-100 px-1">
            {chart.map((item) => (
              <div
                key={item.day}
                className="flex h-full flex-1 flex-col items-center justify-end gap-2"
              >
                <div
                  title={`${item.value}% illustrative activity`}
                  className={`w-full max-w-10 rounded-t-lg ${
                    item.day === "Sat" ? "bg-emerald-700" : "bg-emerald-200"
                  }`}
                  style={{ height: `${item.value}%` }}
                />
                <span className="pb-2 text-xs text-slate-400">
                  {item.day}
                </span>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-500">
            Illustrative activity index, not live employer demand.
          </p>
        </article>

        <article className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
          <SectionTitle
            eyebrow="Workflow"
            title="Demand to learning"
            description="How DemandLock is intended to work"
          />
          <div className="space-y-5">
            {[
              ["01", "Employer submits a need", "A local employer describes a skill and openings."],
              ["02", "Demand is confirmed", "Suggested details are checked by a human."],
              ["03", "A learning pod is proposed", "Training is considered when the demand rule is met."],
              ["04", "Practical progress is reviewed", "Teachers assess tasks and track outcomes."],
            ].map(([n, title, desc]) => (
              <div key={n} className="flex gap-3">
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-emerald-50 text-xs font-bold text-emerald-800">
                  {n}
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-slate-800">{title}</h3>
                  <p className="mt-1 text-sm leading-5 text-slate-500">{desc}</p>
                </div>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <article className="min-w-0 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
          <SectionTitle
            eyebrow="Employer network"
            title="Recent demand"
            description="Fictional records for UI testing"
            action={
              <button
                onClick={() => onNavigate("Employer Demand")}
                className="text-sm font-semibold text-emerald-700"
              >
                See all
              </button>
            }
          />

          {filteredDemands.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[490px] text-left">
                <thead>
                  <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                    <th className="pb-3 font-semibold">Employer / skill</th>
                    <th className="pb-3 font-semibold">Slots</th>
                    <th className="pb-3 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredDemands.map((d) => (
                    <tr key={d.id} className="border-b border-slate-50">
                      <td className="py-4 pr-3">
                        <p className="text-sm font-semibold text-slate-800">{d.company}</p>
                        <p className="mt-1 text-xs text-slate-500">{d.skill}</p>
                      </td>
                      <td className="py-4 text-sm font-semibold text-slate-700">{d.slots}</td>
                      <td className="py-4">
                        <StatusBadge status={d.status} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <article className="min-w-0 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-sm sm:p-6">
          <SectionTitle
            eyebrow="Training"
            title="Active learning pods"
            description="Sample cohort progress"
            action={
              <button
                onClick={() => onNavigate("Learning Pods")}
                className="text-sm font-semibold text-emerald-700"
              >
                View all
              </button>
            }
          />
          {filteredPods.length === 0 ? (
            <EmptyState />
          ) : (
            <div className="space-y-5">
              {filteredPods.map((p) => (
                <div key={p.title}>
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-sm font-semibold text-slate-800">{p.title}</h3>
                      <p className="mt-1 text-xs text-slate-500">
                        {p.learners} demo learners · {p.teacher}
                      </p>
                    </div>
                    <span className="text-sm font-bold text-slate-700">{p.progress}%</span>
                  </div>
                  <div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full ${p.color}`}
                      style={{ width: `${p.progress}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}
        </article>
      </section>

      <section className="mt-8 rounded-2xl border border-emerald-100 bg-emerald-50/70 p-5 sm:p-6">
        <div className="flex items-start gap-4">
          <div className="rounded-xl bg-white p-3 text-emerald-800 shadow-sm">
            <ShieldCheck size={23} />
          </div>
          <div>
            <h3 className="font-semibold text-emerald-950">Trust and verification matter</h3>
            <p className="mt-1 max-w-3xl text-sm leading-6 text-emerald-900/80">
              Keep employer-confirmed demand, learner-reported progress, and verified
              outcomes separate. This prototype uses sample records and does not
              represent real job offers or placements.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}

function EmployerDemandPage({ query, demands, setDemands }) {
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [company, setCompany] = useState("");
  const [skill, setSkill] = useState("");
  const [slots, setSlots] = useState("1");
  const [location, setLocation] = useState("");
  const [message, setMessage] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");
  const [activeModal, setActiveModal] = useState(null);

  const confirmedCount = demands.filter((d) => d.status === "Confirmed").length;
  const reviewCount = demands.filter((d) => d.status === "Needs review").length;

  const filtered = demands.filter((d) => {
    const matchesStatus =
      statusFilter === "All" || d.status === statusFilter;
    const matchesSearch = matchesQuery(
      query,
      d.company,
      d.skill,
      d.status,
      d.location,
      d.slots
    );
    return matchesStatus && matchesSearch;
  });

  function resetForm() {
    setCompany("");
    setSkill("");
    setSlots("1");
    setLocation("");
    setEditingId(null);
    setShowForm(false);
  }

  function startEdit(item) {
    setEditingId(item.id);
    setCompany(item.company);
    setSkill(item.skill);
    setSlots(String(item.slots));
    setLocation(item.location === "Not specified" ? "" : item.location);
    setMessage("");
    setShowForm(true);
  }

  function submitDemand(event) {
    event.preventDefault();

    if (!company.trim() || !skill.trim()) return;

    const updated = {
      id: editingId ?? (
        globalThis.crypto?.randomUUID?.() ||
        `${Date.now()}-${Math.random()}`
      ),
      company: company.trim(),
      skill: skill.trim(),
      location: location.trim() || "Not specified",
      slots: Math.max(1, Number(slots) || 1),
      status: "Needs review",
      initials: company.trim().slice(0, 2).toUpperCase(),
      color: "bg-emerald-100 text-emerald-800",
    };

    if (editingId) {
      setDemands((current) =>
        current.map((d) => (d.id === editingId ? updated : d))
      );
      setMessage("Demand updated. Please reconfirm the updated details.");
    } else {
      setDemands((current) => [updated, ...current]);
      setMessage("Demand added. Employer confirmation is required.");
    }

    resetForm();
  }

  function requestConfirm(item) {
    if (item.status === "Confirmed") return;
    setActiveModal({ type: "confirm", demand: item });
  }

  function requestDelete(item) {
    setActiveModal({ type: "delete", demand: item });
  }

  function closeModal() {
    setActiveModal(null);
  }

  function handleModalAction() {
    if (!activeModal) return;

    const { type, demand } = activeModal;

    if (type === "confirm") {
      setDemands((current) =>
        current.map((item) =>
          item.id === demand.id
            ? { ...item, status: "Confirmed" }
            : item
        )
      );
      setMessage(`Demand from ${demand.company} marked as confirmed.`);
    }

    if (type === "delete") {
      setDemands((current) =>
        current.filter((item) => item.id !== demand.id)
      );

      if (editingId === demand.id) {
        resetForm();
      }

      setMessage(`Demand from ${demand.company} was deleted.`);
    }

    setActiveModal(null);
  }

  return (
    <div className="space-y-6">
      <SectionTitle
        eyebrow="Employer network"
        title="Employer demand"
        description="Record, search, and review local skill requirements."
        action={
          <button
            onClick={() => {
              if (showForm) {
                resetForm();
              } else {
                setMessage("");
                setEditingId(null);
                setCompany("");
                setSkill("");
                setSlots("1");
                setLocation("");
                setShowForm(true);
              }
            }}
            className="rounded-xl bg-emerald-700 px-4 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800"
          >
            {showForm ? "Cancel" : "+ Add demand"}
          </button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          title="Total demands"
          value={demands.length}
          subtitle="All employer records"
          icon={BriefcaseBusiness}
        />
        <StatCard
          title="Confirmed"
          value={confirmedCount}
          subtitle="Marked as confirmed"
          icon={CheckCircle2}
        />
        <StatCard
          title="Needs review"
          value={reviewCount}
          subtitle="Awaiting review"
          icon={ClipboardCheck}
        />
      </div>

      {message && (
        <div className="flex items-start gap-2 rounded-xl border border-emerald-100 bg-emerald-50 p-4 text-sm text-emerald-800">
          <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
          <p>{message}</p>
          <button
            onClick={() => setMessage("")}
            className="ml-auto"
            aria-label="Dismiss message"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {showForm && (
        <form
          onSubmit={submitDemand}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm sm:p-6"
        >
          <h3 className="mb-5 text-lg font-bold text-slate-900">
            {editingId ? "Edit employer demand" : "Add employer demand"}
          </h3>

          <div className="grid gap-4 sm:grid-cols-2">
            <label className="text-sm font-medium text-slate-700">
              Employer name *
              <input
                required
                maxLength={100}
                value={company}
                onChange={(e) => setCompany(e.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-emerald-600"
                placeholder="e.g. GreenLeaf Organics"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Skill needed *
              <input
                required
                maxLength={100}
                value={skill}
                onChange={(e) => setSkill(e.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-emerald-600"
                placeholder="e.g. Digital Marketing"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Number of openings *
              <input
                type="number"
                min="1"
                max="10000"
                required
                value={slots}
                onChange={(e) => setSlots(e.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-emerald-600"
              />
            </label>

            <label className="text-sm font-medium text-slate-700">
              Location
              <input
                maxLength={120}
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-emerald-600"
                placeholder="Village, town, or locality"
              />
            </label>
          </div>

          <p className="mt-4 text-xs leading-5 text-slate-500">
            New or edited demands return to “Needs review.” Confirm only after
            the employer's requirements have been checked.
          </p>

          <div className="mt-5 flex flex-wrap gap-3">
            <button
              type="submit"
              className="rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800"
            >
              {editingId ? "Save changes" : "Add demand"}
            </button>
            <button
              type="button"
              onClick={resetForm}
              className="rounded-xl border border-slate-200 px-5 py-2.5 text-sm font-semibold text-slate-600 hover:bg-slate-50"
            >
              Cancel
            </button>
          </div>
        </form>
      )}

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
        <div className="p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h3 className="font-semibold text-slate-900">Demand records</h3>
              <p className="mt-1 text-xs text-slate-500">
                Showing {filtered.length} of {demands.length} records
              </p>
            </div>
            <span className="flex items-center gap-2 text-xs text-slate-500">
              <SlidersHorizontal size={15} />
              Filter by status or search
            </span>
          </div>

          <div className="mt-5 flex flex-wrap gap-2">
            {[
              { label: "All demands", value: "All", count: demands.length },
              { label: "Confirmed", value: "Confirmed", count: confirmedCount },
              { label: "Needs review", value: "Needs review", count: reviewCount },
            ].map((filter) => (
              <button
                key={filter.value}
                type="button"
                onClick={() => setStatusFilter(filter.value)}
                className={`inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-medium transition ${
                  statusFilter === filter.value
                    ? "border-emerald-700 bg-emerald-700 text-white shadow-sm"
                    : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
                }`}
              >
                {filter.label}
                <span
                  className={`rounded-full px-2 py-0.5 text-xs ${
                    statusFilter === filter.value
                      ? "bg-white/20 text-white"
                      : "bg-slate-100 text-slate-600"
                  }`}
                >
                  {filter.count}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto border-t border-slate-100">
          {filtered.length === 0 ? (
            <div className="p-5">
              <EmptyState message="No employer demands match your filters." />
            </div>
          ) : (
            <table className="w-full min-w-[850px] text-left">
              <thead className="bg-slate-50">
                <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                  <th className="px-5 py-4 font-semibold">Employer</th>
                  <th className="px-4 py-4 font-semibold">Skill</th>
                  <th className="px-4 py-4 font-semibold">Location</th>
                  <th className="px-4 py-4 font-semibold">Openings</th>
                  <th className="px-4 py-4 font-semibold">Status</th>
                  <th className="px-5 py-4 font-semibold">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-slate-50 last:border-0 hover:bg-slate-50/60"
                  >
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-3">
                        <div
                          className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-xs font-bold ${
                            item.color || "bg-emerald-100 text-emerald-800"
                          }`}
                        >
                          {item.initials || item.company.slice(0, 2).toUpperCase()}
                        </div>
                        <span className="text-sm font-semibold text-slate-800">
                          {item.company}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-4 text-sm text-slate-600">{item.skill}</td>
                    <td className="px-4 py-4 text-sm text-slate-600">{item.location}</td>
                    <td className="px-4 py-4 text-sm font-semibold text-slate-700">{item.slots}</td>
                    <td className="px-4 py-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center gap-2">
                        {item.status !== "Confirmed" && (
                          <button
                            type="button"
                            onClick={() => requestConfirm(item)}
                            title="Confirm demand"
                            aria-label={`Confirm demand from ${item.company}`}
                            className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-700 px-3 py-2 text-xs font-semibold text-white transition hover:bg-emerald-800"
                          >
                            <CheckCircle2 size={15} />
                            Confirm
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() => startEdit(item)}
                          title="Edit demand"
                          aria-label={`Edit demand from ${item.company}`}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 transition hover:bg-slate-100"
                        >
                          <Pencil size={14} />
                          Edit
                        </button>

                        <button
                          type="button"
                          onClick={() => requestDelete(item)}
                          title="Delete demand"
                          aria-label={`Delete demand from ${item.company}`}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 px-3 py-2 text-xs font-semibold text-red-600 transition hover:bg-red-50"
                        >
                          <Trash2 size={14} />
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        <p className="px-5 py-4 text-xs leading-5 text-slate-400">
          Changes are held in React state only and reset on refresh. No backend is connected.
        </p>
      </div>

      {/* Custom Confirm / Delete Modal */}
      {activeModal && (
        <div
          className="fixed inset-0 z-[100] flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) closeModal();
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="demand-modal-title"
            className="w-full max-w-md overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl"
          >
            <div className="flex items-start gap-4 p-6">
              <div
                className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${
                  activeModal.type === "delete"
                    ? "bg-red-50 text-red-600"
                    : "bg-emerald-50 text-emerald-700"
                }`}
              >
                {activeModal.type === "delete" ? (
                  <Trash2 size={23} />
                ) : (
                  <CheckCircle2 size={23} />
                )}
              </div>

              <div className="min-w-0 flex-1">
                <h3
                  id="demand-modal-title"
                  className="text-lg font-bold text-slate-900"
                >
                  {activeModal.type === "delete"
                    ? "Delete employer demand?"
                    : "Confirm employer demand"}
                </h3>
                <p className="mt-1 text-sm leading-6 text-slate-500">
                  {activeModal.type === "delete"
                    ? "This will remove the demand from your current demo workspace."
                    : "Confirm that this employer skill requirement is ready for planning."}
                </p>
              </div>

              <button
                type="button"
                onClick={closeModal}
                aria-label="Close dialog"
                className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <X size={19} />
              </button>
            </div>

            <div className="mx-6 rounded-xl border border-slate-200 bg-slate-50 p-4">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">
                Employer
              </p>
              <p className="mt-1 font-semibold text-slate-900">
                {activeModal.demand.company}
              </p>

              <div className="mt-3 grid grid-cols-2 gap-3">
                <div>
                  <p className="text-xs text-slate-500">Skill needed</p>
                  <p className="mt-1 text-sm font-medium text-slate-700">
                    {activeModal.demand.skill}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Openings</p>
                  <p className="mt-1 text-sm font-medium text-slate-700">
                    {activeModal.demand.slots}
                  </p>
                </div>
              </div>

              <div className="mt-3">
                <StatusBadge status={activeModal.demand.status} />
              </div>
            </div>

            <div className="flex flex-col-reverse gap-3 p-6 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={closeModal}
                className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50"
              >
                Cancel
              </button>

              <button
                type="button"
                autoFocus
                onClick={handleModalAction}
                className={`inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white transition ${
                  activeModal.type === "delete"
                    ? "bg-red-600 hover:bg-red-700"
                    : "bg-emerald-700 hover:bg-emerald-800"
                }`}
              >
                {activeModal.type === "delete" ? (
                  <>
                    <Trash2 size={16} />
                    Delete demand
                  </>
                ) : (
                  <>
                    <CheckCircle2 size={16} />
                    Confirm demand
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function PodsPage({ query }) {
  const filtered = pods.filter((p) =>
    matchesQuery(query, p.title, p.teacher, p.tag)
  );

  return (
    <div>
      <SectionTitle
        eyebrow="Teacher-led training"
        title="Learning pods"
        description="Explore practical learning cohorts and their progress."
      />
      {filtered.length === 0 ? (
        <EmptyState />
      ) : (
        <div className="grid gap-5 lg:grid-cols-2">
          {filtered.map((p) => (
            <article
              key={p.title}
              className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
            >
              <div className="flex items-start justify-between gap-4">
                <div className={`rounded-xl p-3 text-white ${p.color}`}>
                  <BookOpen size={23} />
                </div>
                <StatusBadge status={p.tag} />
              </div>
              <h3 className="mt-5 text-lg font-bold text-slate-900">{p.title}</h3>
              <p className="mt-2 text-sm text-slate-500">{p.teacher}</p>
              <p className="mt-4 text-sm text-slate-600">
                {p.learners} sample learners
              </p>
              <div className="mt-4 flex justify-between text-sm">
                <span className="text-slate-500">Task progress</span>
                <strong>{p.progress}%</strong>
              </div>
              <div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100">
                <div
                  className={`h-full rounded-full ${p.color}`}
                  style={{ width: `${p.progress}%` }}
                />
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}

function LearnersPage({ query }) {
  const filtered = learners.filter((l) =>
    matchesQuery(query, l.id, l.name, l.skill, l.pod, l.progress)
  );

  return (
    <div>
      <SectionTitle
        eyebrow="Learning progress"
        title="Learners"
        description="Search sample learners by name, ID, skill, or pod."
      />

      <div className="mb-6 grid gap-4 sm:grid-cols-3">
        <StatCard title="Demo learners" value="35" subtitle="Sample cohort count" icon={Users} />
        <StatCard title="Tasks started" value="24" subtitle="Illustrative count" icon={ClipboardCheck} />
        <StatCard title="Task completion" value="68%" subtitle="Illustrative average" icon={CheckCircle2} />
      </div>

      <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        {filtered.length === 0 ? (
          <EmptyState message="No learners match your search." />
        ) : (
          <table className="w-full min-w-[620px] text-left">
            <thead>
              <tr className="border-b border-slate-100 text-xs uppercase tracking-wide text-slate-400">
                <th className="pb-4 font-semibold">Learner</th>
                <th className="pb-4 font-semibold">Skill</th>
                <th className="pb-4 font-semibold">Learning pod</th>
                <th className="pb-4 font-semibold">Progress</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((l) => (
                <tr key={l.id} className="border-b border-slate-50">
                  <td className="py-4 pr-3">
                    <p className="text-sm font-semibold text-slate-800">{l.name}</p>
                    <p className="mt-1 text-xs text-slate-400">{l.id}</p>
                  </td>
                  <td className="py-4 pr-3 text-sm text-slate-600">{l.skill}</td>
                  <td className="py-4 pr-3 text-sm text-slate-600">{l.pod}</td>
                  <td className="py-4">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-20 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className="h-full rounded-full bg-emerald-600"
                          style={{ width: `${l.progress}%` }}
                        />
                      </div>
                      <span className="text-xs font-semibold text-slate-600">
                        {l.progress}%
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
        <p className="mt-4 text-xs text-slate-400">
          All learner records shown here are fictional demo data.
        </p>
      </div>
    </div>
  );
}

function TeacherReviewPage({ query }) {
  const [reviewed, setReviewed] = useState([]);

  const filtered = tasks.filter((t) =>
    matchesQuery(
      query,
      t.name,
      t.learner,
      t.skill,
      reviewed.includes(t.id) ? "Reviewed" : "Needs review"
    )
  );

  return (
    <div>
      <SectionTitle
        eyebrow="Practical assessment"
        title="Teacher review"
        description="Search sample tasks, then mark them as reviewed."
      />
      <div className="space-y-3">
        {filtered.length === 0 ? (
          <EmptyState message="No tasks match your search." />
        ) : (
          filtered.map((t) => {
            const done = reviewed.includes(t.id);

            return (
              <article
                key={t.id}
                className="flex flex-col justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-5 sm:flex-row sm:items-center"
              >
                <div>
                  <h3 className="font-semibold text-slate-900">{t.name}</h3>
                  <p className="mt-1 text-sm text-slate-500">
                    {t.learner} · {t.skill}
                  </p>
                  <div className="mt-2">
                    <StatusBadge status={done ? "Reviewed" : "Needs review"} />
                  </div>
                </div>
                <button
                  onClick={() =>
                    setReviewed((current) =>
                      done
                        ? current.filter((id) => id !== t.id)
                        : [...current, t.id]
                    )
                  }
                  className={`flex items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold ${
                    done
                      ? "bg-emerald-50 text-emerald-800"
                      : "bg-emerald-700 text-white hover:bg-emerald-800"
                  }`}
                >
                  <CheckCircle2 size={17} />
                  {done ? "Undo review" : "Mark reviewed"}
                </button>
              </article>
            );
          })
        )}
      </div>
      <p className="mt-4 text-xs text-slate-500">
        Review states are temporary and are not saved to a backend.
      </p>
    </div>
  );
}

function ImpactPage({ query }) {
  const filtered = outcomes.filter((o) =>
    matchesQuery(query, o.title, o.category, o.status, o.value)
  );

  return (
    <div>
      <SectionTitle
        eyebrow="Outcomes"
        title="Impact & outcomes"
        description="Search outcome stages and distinguish verified outcomes from sample figures."
      />

      {filtered.length === 0 ? (
        <EmptyState message="No outcome categories match your search." />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {filtered.map((o) => (
            <article
              key={o.title}
              className="rounded-2xl border border-slate-200 bg-white p-5"
            >
              <p className="text-sm text-slate-500">{o.title}</p>
              <p className="mt-3 text-3xl font-bold text-slate-900">{o.value}</p>
              <p className="mt-3 text-xs font-semibold text-amber-700">{o.status}</p>
              <p className="mt-1 text-xs text-slate-400">{o.category}</p>
            </article>
          ))}
        </div>
      )}

      <div className="mt-6 rounded-2xl border border-amber-200 bg-amber-50 p-5">
        <h3 className="font-semibold text-amber-950">Demo data, not real impact</h3>
        <p className="mt-2 text-sm leading-6 text-amber-900">
          These figures are fictional examples. Real outcomes require evidence
          and appropriate verification before being reported as actual results.
        </p>
      </div>
    </div>
  );
}

function SettingsPage({ profileName, setProfileName, role, setRole }) {
  const [saved, setSaved] = useState(false);

  return (
    <div>
      <SectionTitle
        eyebrow="Preferences"
        title="Settings"
        description="Manage the local demo profile and workspace preferences."
      />
      <div className="max-w-2xl rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3 border-b border-slate-100 pb-5">
          <div className="rounded-xl bg-emerald-50 p-3 text-emerald-700">
            <SlidersHorizontal size={22} />
          </div>
          <div>
            <h3 className="font-semibold text-slate-900">Profile preferences</h3>
            <p className="mt-1 text-sm text-slate-500">
              These settings are held in the current page session only.
            </p>
          </div>
        </div>

        <form
          className="mt-5 space-y-5"
          onSubmit={(e) => {
            e.preventDefault();
            setSaved(true);
          }}
        >
          <label className="block text-sm font-medium text-slate-700">
            Display name
            <input
              value={profileName}
              onChange={(e) => {
                setProfileName(e.target.value);
                setSaved(false);
              }}
              className="mt-2 w-full rounded-xl border border-slate-200 px-3 py-2.5 outline-none focus:border-emerald-600"
            />
          </label>

          <label className="block text-sm font-medium text-slate-700">
            Workspace role
            <select
              value={role}
              onChange={(e) => {
                setRole(e.target.value);
                setSaved(false);
              }}
              className="mt-2 w-full rounded-xl border border-slate-200 bg-white px-3 py-2.5 outline-none focus:border-emerald-600"
            >
              <option>Administrator</option>
              <option>Employer</option>
              <option>Teacher</option>
              <option>Coordinator</option>
            </select>
          </label>

          <button
            type="submit"
            className="rounded-xl bg-emerald-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-emerald-800"
          >
            Save preferences
          </button>
          {saved && (
            <p className="text-sm text-emerald-700">
              Preferences updated for this session.
            </p>
          )}
        </form>

        <p className="mt-5 border-t border-slate-100 pt-4 text-xs leading-5 text-slate-400">
          This prototype does not have authentication, account management, or persistent settings yet.
        </p>
      </div>
    </div>
  );
}

function App() {
  const [activePage, setActivePage] = useState("Overview");
  const [query, setQuery] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [profileName, setProfileName] = useState("Demo Profile");
  const [role, setRole] = useState("Administrator");

  const [demands, setDemands] = useState(() =>
    initialDemands.map((d, i) => ({ ...d, id: `seed-${i + 1}` }))
  );

  const pageContent = useMemo(() => {
    switch (activePage) {
      case "Employer Demand":
        return (
          <EmployerDemandPage
            query={query}
            demands={demands}
            setDemands={setDemands}
          />
        );
      case "Learning Pods":
        return <PodsPage query={query} />;
      case "Learners":
        return <LearnersPage query={query} />;
      case "Teacher Review":
        return <TeacherReviewPage query={query} />;
      case "Impact & Outcomes":
        return <ImpactPage query={query} />;
      case "Settings":
        return (
          <SettingsPage
            profileName={profileName}
            setProfileName={setProfileName}
            role={role}
            setRole={setRole}
          />
        );
      default:
        return (
          <Overview
            onNavigate={setActivePage}
            query={query}
            demands={demands}
          />
        );
    }
  }, [activePage, query, demands, profileName, role]);

  function navigate(page) {
    setActivePage(page);
    setSidebarOpen(false);
    setProfileOpen(false);
    setQuery("");
  }

  return (
    <div className="min-h-screen bg-[#f6f8f6]">
      {sidebarOpen && (
        <button
          className="fixed inset-0 z-40 bg-slate-950/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-label="Close navigation"
        />
      )}

      <aside
        className={`fixed inset-y-0 left-0 z-50 flex w-[270px] flex-col bg-[#142b23] transition-transform duration-200 lg:translate-x-0 ${
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        }`}
      >
        <div className="flex h-[76px] items-center gap-3 border-b border-white/10 px-5">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-400 text-emerald-950">
            <Activity size={23} strokeWidth={2.5} />
          </div>
          <div>
            <p className="text-base font-bold tracking-tight text-white">DemandLock</p>
            <p className="text-xs text-emerald-100/70">Skills to opportunities</p>
          </div>
          <button
            className="ml-auto rounded-lg p-2 text-slate-300 hover:bg-white/10 lg:hidden"
            onClick={() => setSidebarOpen(false)}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        <div className="px-4 pt-7">
          <p className="px-3 text-[10px] font-bold uppercase tracking-[0.18em] text-slate-400">
            Workspace
          </p>
          <nav className="mt-3 space-y-1">
            {navItems.map(({ label, icon: Icon }) => {
              const active = activePage === label;

              return (
                <button
                  key={label}
                  onClick={() => navigate(label)}
                  className={`flex w-full items-center gap-3 rounded-xl px-3 py-3 text-left text-sm font-medium transition ${
                    active
                      ? "bg-emerald-400 text-emerald-950 shadow-sm"
                      : "text-slate-300 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  <Icon size={18} />
                  <span>{label}</span>
                  {active && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-emerald-950" />
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="mt-auto p-4">
          <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
            <div className="flex items-center gap-2 text-emerald-200">
              <CircleHelp size={17} />
              <p className="text-sm font-semibold">Demo workspace</p>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-300">
              Sample records only. Connect the team API before using real data.
            </p>
          </div>
          <p className="px-3 pt-5 text-[10px] text-slate-500">
            DEMANDLOCK PODS · PROTOTYPE
          </p>
        </div>
      </aside>

      <div className="min-h-screen lg:pl-[270px]">
        <header className="sticky top-0 z-30 flex h-[76px] items-center justify-between gap-3 border-b border-slate-200/80 bg-white/95 px-4 backdrop-blur sm:px-7 lg:px-9">
          <div className="flex min-w-0 items-center gap-3">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-slate-600 hover:bg-slate-100 lg:hidden"
              aria-label="Open navigation"
            >
              <Menu size={22} />
            </button>
            <div className="min-w-0">
              <div className="flex items-center gap-2 text-xs text-slate-400">
                <span>Workspace</span>
                <span>/</span>
                <span className="truncate text-slate-600">{activePage}</span>
              </div>
              <p className="mt-1 truncate text-sm font-bold text-slate-900 sm:text-base">
                {activePage === "Overview" ? "Dashboard overview" : activePage}
              </p>
            </div>
          </div>

          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <label className="hidden w-52 items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 md:flex">
              <Search size={16} className="shrink-0 text-slate-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={`Search ${activePage.toLowerCase()}...`}
                className="w-full min-w-0 bg-transparent text-xs outline-none placeholder:text-slate-400"
                aria-label={`Search ${activePage}`}
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  aria-label="Clear search"
                  className="text-slate-400 hover:text-slate-700"
                >
                  <X size={14} />
                </button>
              )}
            </label>

            <button
              onClick={() => setNotificationsOpen((v) => !v)}
              className="relative rounded-xl border border-slate-200 p-2.5 text-slate-600 hover:bg-slate-50"
              aria-label="Notifications"
              aria-expanded={notificationsOpen}
            >
              <Bell size={18} />
              <span className="absolute right-2 top-2 h-2 w-2 rounded-full border-2 border-white bg-amber-500" />
            </button>

            <div className="relative">
              <button
                onClick={() => setProfileOpen((v) => !v)}
                className="flex items-center gap-2 rounded-xl p-1.5 hover:bg-slate-50"
                aria-label="Open profile menu"
                aria-expanded={profileOpen}
              >
                <div className="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-xs font-bold text-emerald-800">
                  {profileName.trim().slice(0, 2).toUpperCase() || "DP"}
                </div>
                <div className="hidden text-left xl:block">
                  <p className="max-w-28 truncate text-xs font-semibold text-slate-800">
                    {profileName}
                  </p>
                  <p className="mt-0.5 text-[10px] text-slate-500">{role}</p>
                </div>
                <ChevronDown size={15} className="hidden text-slate-400 sm:block" />
              </button>

              {profileOpen && (
                <div className="absolute right-0 top-full z-50 mt-3 w-60 rounded-xl border border-slate-200 bg-white p-2 shadow-xl">
                  <div className="border-b border-slate-100 px-3 py-3">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-emerald-100 text-sm font-bold text-emerald-800">
                        {profileName.trim().slice(0, 2).toUpperCase() || "DP"}
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-sm font-semibold text-slate-900">{profileName}</p>
                        <p className="mt-1 text-xs text-slate-500">{role}</p>
                      </div>
                    </div>
                  </div>
                  <button
                    onClick={() => navigate("Overview")}
                    className="mt-1 flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50"
                  >
                    <UserRound size={16} /> Dashboard
                  </button>
                  <button
                    onClick={() => navigate("Settings")}
                    className="flex w-full items-center gap-2 rounded-lg px-3 py-2.5 text-left text-sm text-slate-700 hover:bg-slate-50"
                  >
                    <SettingsIcon size={16} /> Profile &amp; settings
                  </button>
                  <p className="border-t border-slate-100 px-3 py-2 text-xs text-slate-400">
                    Demo account · No authentication
                  </p>
                </div>
              )}
            </div>
          </div>
        </header>

        {notificationsOpen && (
          <div className="relative z-20 border-b border-slate-200 bg-amber-50 px-5 py-3 text-sm text-amber-900 sm:px-9">
            <div className="flex items-center gap-2">
              <Bell size={17} />
              <span>
                Demo notification: review the sample employer demand marked “Needs review”.
              </span>
              <button
                onClick={() => setNotificationsOpen(false)}
                className="ml-auto font-semibold underline"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        <main className="mx-auto max-w-[1600px] px-4 py-7 sm:px-7 sm:py-8 lg:px-9">
          <div className="mb-7 flex flex-wrap items-center justify-between gap-3">
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-950 sm:text-[28px]">
                Good to see you
              </h1>
              <p className="mt-2 text-sm text-slate-500">
                Here is a snapshot of the DemandLock demo workspace.
              </p>
            </div>
            <span className="inline-flex items-center gap-2 rounded-full border border-amber-200 bg-amber-50 px-3 py-2 text-xs font-semibold text-amber-800">
              <span className="h-2 w-2 rounded-full bg-amber-500" />
              Demo mode · Not live data
            </span>
          </div>

          <div className="mb-6 md:hidden">
            <label className="flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-3 py-3">
              <Search size={17} className="text-slate-400" />
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={`Search ${activePage.toLowerCase()}...`}
                className="w-full bg-transparent text-sm outline-none"
                aria-label={`Search ${activePage}`}
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery("")}
                  aria-label="Clear search"
                  className="text-slate-400"
                >
                  <X size={15} />
                </button>
              )}
            </label>
          </div>

          {pageContent}

          <footer className="mt-10 flex flex-col justify-between gap-2 border-t border-slate-200 pt-5 text-xs text-slate-400 sm:flex-row">
            <p>DemandLock Pods · Frontend prototype</p>
            <p>Demo data only · Backend integration pending</p>
          </footer>
        </main>
      </div>
    </div>
  );
}

export default App;
