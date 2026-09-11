"use client";

import { useCallback, useEffect, useState } from "react";
import type { ComponentProps, ReactNode } from "react";
import { ChevronDown, Check, Gauge, MessageSquareText, Trash2, UploadCloud } from "lucide-react";
import { Area, AreaChart, Bar, BarChart, CartesianGrid, Cell, XAxis, YAxis } from "recharts";

import { Badge as ReferenceBadge } from "@/components/badge";
import { Button as ReferenceButton } from "@/components/button";
import { Card as ReferenceCard, CardContent, CardDescription, CardHeader as ReferenceCardHeader, CardTitle } from "@/components/card";
import { ChartContainer as ReferenceChartContainer, ChartTooltip, ChartTooltipContent as ReferenceChartTooltipContent, INITIAL_DIMENSION, type ChartConfig } from "@/components/chart";
import { Input } from "@/components/input";
import { ConfirmDialog } from "@/components/confirm-dialog";
import { ScrollableTabsList } from "@/components/scrollable-tabs-list";
import { Tabs, TabsContent, TabsTrigger } from "@/components/tabs";
import { DateRange, deleteAllMessages, getMessages, getSummary, importChat, Message, Sentiment, Summary } from "@/lib/api";

type AppCardProps = Omit<ComponentProps<typeof ReferenceCard>, "size"> & { size?: "default" | "sm" };
function Card({ size = "default", ...props }: AppCardProps) {
  return <ReferenceCard size={size} {...props} />;
}

type AppCardHeaderProps = Omit<ComponentProps<typeof ReferenceCardHeader>, "divider"> & { divider?: boolean };
function CardHeader({ divider = false, ...props }: AppCardHeaderProps) {
  return <ReferenceCardHeader divider={divider} {...props} />;
}

type AppBadgeProps = Omit<ComponentProps<typeof ReferenceBadge>, "asChild" | "shape" | "size" | "tone" | "type"> & {
  asChild?: boolean;
  shape?: "pill" | "chip";
  size?: "sm" | "md";
  tone?: "brand" | "neutral" | "app" | "info" | "success" | "warning" | "danger" | "processing";
  type?: "soft" | "solid" | "outline" | "plain";
};
function Badge({ asChild = false, shape = "pill", size = "sm", tone = "neutral", type = "soft", ...props }: AppBadgeProps) {
  return <ReferenceBadge asChild={asChild} shape={shape} size={size} tone={tone} type={type} {...props} />;
}

type AppButtonProps = Omit<Partial<ComponentProps<typeof ReferenceButton>>, "asChild" | "fullWidth" | "iconOnly" | "loading" | "size" | "tone" | "type" | "variant"> & {
  asChild?: boolean;
  fullWidth?: boolean;
  iconOnly?: boolean;
  loading?: boolean;
  size?: "sm" | "md" | "lg";
  tone?: "neutral" | "app" | "danger" | "success" | "warning";
  type?: "button" | "submit" | "reset";
  variant?: "primary" | "secondary" | "tertiary" | "plain" | "link";
  children?: ReactNode;
};
function Button({ asChild = false, fullWidth = false, iconOnly = false, loading = false, size = "md", tone = "neutral", type = "button", variant = "primary", ...props }: AppButtonProps) {
  return <ReferenceButton asChild={asChild} fullWidth={fullWidth} iconOnly={iconOnly} loading={loading} size={size} tone={tone} type={type} variant={variant} {...props} />;
}

type AppChartContainerProps = Omit<ComponentProps<typeof ReferenceChartContainer>, "initialDimension"> & { initialDimension?: { width: number; height: number } };
function ChartContainer({ initialDimension = INITIAL_DIMENSION, ...props }: AppChartContainerProps) {
  return <ReferenceChartContainer initialDimension={initialDimension} {...props} />;
}

type AppChartTooltipContentProps = Partial<ComponentProps<typeof ReferenceChartTooltipContent>>;
function ChartTooltipContent({ hideLabel = false, hideIndicator = false, indicator = "dot", ...props }: AppChartTooltipContentProps) {
  return <ReferenceChartTooltipContent hideLabel={hideLabel} hideIndicator={hideIndicator} indicator={indicator} {...props} />;
}

const emptySummary: Summary = { period_days: 7, range_start: "", range_end: "", total_messages: 0, counts: { positive: 0, neutral: 0, negative: 0, unknown: 0 }, negative_last_24h: 0, negative_spike: false, alerts: [], trend: [], emotions: [] };
const trendConfig: ChartConfig = {
  positive: { label: "Positif", color: "var(--brand-teal-strong)" },
  neutral: { label: "Neutre", color: "#64748b" },
  negative: { label: "Négatif", color: "var(--danger)" },
};
const emotionConfig: ChartConfig = { count: { label: "Messages", color: "var(--brand-orange)" } };
const sentimentLabels: Record<Sentiment, string> = { positive: "Positif", neutral: "Neutre", negative: "Négatif", unknown: "Inconnu" };
const emotionLabels: Record<string, string> = { frustration: "Frustration", joy: "Joie", excitement: "Enthousiasme", neutral: "Neutre", gratitude: "Gratitude", confusion: "Confusion", anger: "Colère", sadness: "Tristesse", other: "Autre" };
const emotionColors: Record<string, string> = {
  frustration: "var(--danger)",
  joy: "#f5b82e",
  excitement: "#c05ee8",
  neutral: "#64748b",
  gratitude: "var(--brand-teal-strong)",
  confusion: "#4f8fe8",
};
const windowOptions = [
  { value: 1, label: "Dernières 24 heures" },
  { value: 7, label: "Derniers 7 jours" },
  { value: 30, label: "Derniers 30 jours" },
  { value: 90, label: "Derniers 90 jours" },
];
const sentimentOptions = [
  { value: "", label: "Tous les sentiments" },
  { value: "positive", label: "Positif" },
  { value: "neutral", label: "Neutre" },
  { value: "negative", label: "Négatif" },
  { value: "unknown", label: "Inconnu" },
];

function formatDate(value: string) { return new Intl.DateTimeFormat("fr-FR", { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }).format(new Date(value)); }
function formatEmotion(value: string) { return emotionLabels[value.toLowerCase()] || value; }
function formatShortDate(value: string) { return value ? new Intl.DateTimeFormat("fr-FR", { day: "numeric", month: "short", year: "numeric" }).format(new Date(`${value}T00:00:00`)) : ""; }
function describeRange(summary: Summary) { return summary.range_start && summary.range_end ? `du ${formatShortDate(summary.range_start)} au ${formatShortDate(summary.range_end)}` : "la période sélectionnée"; }

function SentimentBadge({ label }: { label: Sentiment }) {
  const tone = label === "positive" ? "success" : label === "negative" ? "danger" : label === "unknown" ? "warning" : "neutral";
  return <Badge tone={tone}>{sentimentLabels[label]}</Badge>;
}

function WindowSelect({ days, onChange }: { days: number; onChange: (value: number) => void }) {
  const [open, setOpen] = useState(false);
  const current = windowOptions.find((option) => option.value === days) || windowOptions[1];
  return <div className="relative min-w-48"><button type="button" aria-expanded={open} aria-haspopup="listbox" aria-label="Période de synthèse" className="flex h-9 w-full items-center justify-between gap-3 rounded-md border border-border bg-muted/50 px-3 text-sm text-foreground outline-none transition-colors hover:bg-muted focus:ring-2 focus:ring-[var(--brand-teal-action)]" onClick={() => setOpen((value) => !value)}>{current.label}<ChevronDown className={`size-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} /></button>{open && <div aria-label="Options de période" className="absolute right-0 z-20 mt-2 w-full overflow-hidden rounded-lg border border-border bg-popover p-1 text-popover-foreground shadow-lg" role="listbox">{windowOptions.map((option) => <button key={option.value} type="button" aria-selected={option.value === days} className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--brand-teal-soft)] hover:text-[var(--brand-teal-strong)] ${option.value === days ? "bg-[var(--brand-teal-soft)] font-medium text-[var(--brand-teal-strong)]" : "text-muted-foreground"}`} onClick={() => { onChange(option.value); setOpen(false); }}>{option.label}{option.value === days && <Check className="size-4" />}</button>)}</div>}</div>;
}

function PeriodFilter({ days, dateRange, onDays, onRange, onClearRange }: { days: number; dateRange: DateRange | null; onDays: (value: number) => void; onRange: (value: DateRange) => void; onClearRange: () => void }) {
  const [open, setOpen] = useState(false);
  const [from, setFrom] = useState(dateRange?.from ?? "");
  const [to, setTo] = useState(dateRange?.to ?? "");
  useEffect(() => { setFrom(dateRange?.from ?? ""); setTo(dateRange?.to ?? ""); }, [dateRange]);

  if (dateRange) {
    return <div className="flex flex-wrap items-center gap-2"><Badge tone="info" type="soft">Du {formatShortDate(dateRange.from)} au {formatShortDate(dateRange.to)}</Badge><Button onClick={onClearRange} size="sm" variant="tertiary">Revenir aux périodes prédéfinies</Button></div>;
  }
  return <div className="flex flex-wrap items-center gap-2"><WindowSelect days={days} onChange={onDays} /><div className="relative"><Button onClick={() => setOpen((value) => !value)} size="sm" variant="secondary">Plage personnalisée</Button>{open && <div aria-label="Choisir une plage de dates" className="absolute right-0 z-20 mt-2 flex w-max flex-wrap items-center gap-2 rounded-lg border border-border bg-popover p-3 text-popover-foreground shadow-lg" role="dialog">{/* Sorti du flux (absolute) pour ne pas déplacer les éléments autour quand il s'ouvre. */}<Input aria-label="Date de début" max={to || undefined} onChange={(event) => setFrom(event.target.value)} type="date" value={from} /><span className="text-xs text-muted-foreground">au</span><Input aria-label="Date de fin" min={from || undefined} onChange={(event) => setTo(event.target.value)} type="date" value={to} /><Button disabled={!from || !to || from > to} onClick={() => { onRange({ from, to }); setOpen(false); }} size="sm">Appliquer</Button></div>}</div></div>;
}

function SentimentSelect({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const [open, setOpen] = useState(false);
  const current = sentimentOptions.find((option) => option.value === value) || sentimentOptions[0];
  return <div className="relative min-w-48"><button type="button" aria-expanded={open} aria-haspopup="listbox" aria-label="Filtrer par sentiment" className="flex h-10 w-full items-center justify-between gap-3 rounded-md border border-border bg-muted/50 px-3 text-sm text-foreground outline-none transition-colors hover:bg-muted focus:ring-2 focus:ring-[var(--brand-teal-action)]" onClick={() => setOpen((isOpen) => !isOpen)}>{current.label}<ChevronDown className={`size-4 text-muted-foreground transition-transform ${open ? "rotate-180" : ""}`} /></button>{open && <div aria-label="Options de sentiment" className="absolute right-0 z-20 mt-2 w-full overflow-hidden rounded-lg border border-border bg-popover p-1 text-popover-foreground shadow-lg" role="listbox">{sentimentOptions.map((option) => <button key={option.value || "all"} type="button" aria-selected={option.value === value} className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-[var(--brand-teal-soft)] hover:text-[var(--brand-teal-strong)] ${option.value === value ? "bg-[var(--brand-teal-soft)] font-medium text-[var(--brand-teal-strong)]" : "text-muted-foreground"}`} onClick={() => { onChange(option.value); setOpen(false); }}>{option.label}{option.value === value && <Check className="size-4" />}</button>)}</div>}</div>;
}

function Metrics({ summary }: { summary: Summary }) {
  const total = summary.counts.positive + summary.counts.neutral + summary.counts.negative;
  return <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">{[
    ["Total de messages", summary.total_messages, "Période sélectionnée", "neutral"],
    ["Positif", summary.counts.positive, `${total ? Math.round(summary.counts.positive / total * 100) : 0}% des messages classés`, "success"],
    ["Neutre", summary.counts.neutral, `${total ? Math.round(summary.counts.neutral / total * 100) : 0}% des messages classés`, "neutral"],
    ["Négatif", summary.counts.negative, `${total ? Math.round(summary.counts.negative / total * 100) : 0}% des messages classés`, "danger"],
  ].map(([label, value, note, tone]) => <Card className="shadow-xs" key={String(label)}><CardHeader divider={false} className="pb-0"><CardDescription className="flex items-center gap-2"><span className={`size-2 rounded-full ${tone === "success" ? "bg-[var(--success)]" : tone === "danger" ? "bg-[var(--danger)]" : "bg-muted-foreground"}`} />{label}</CardDescription><CardTitle className="mt-2 text-3xl font-semibold tabular-nums">{Number(value).toLocaleString("fr-FR")}</CardTitle></CardHeader><CardContent className="pt-2 text-xs text-muted-foreground">{note}</CardContent></Card>)};</section>;
}

function OverviewTab({ summary, days, dateRange, onDaysChange, onRangeChange, onClearRange }: { summary: Summary; days: number; dateRange: DateRange | null; onDaysChange: (value: number) => void; onRangeChange: (value: DateRange) => void; onClearRange: () => void }) {
  const emotions = summary.emotions.slice(0, 8).map((entry) => ({ ...entry, label: formatEmotion(entry.emotion) }));
  return <div className="flex flex-col gap-4"><div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between"><div><h2 className="text-lg font-semibold">Vue d’ensemble</h2><p className="text-sm text-muted-foreground">Synthèse {describeRange(summary)}</p></div><PeriodFilter days={days} dateRange={dateRange} onClearRange={onClearRange} onDays={onDaysChange} onRange={onRangeChange} /></div><Metrics summary={summary} /><Card><CardHeader divider={false}><CardTitle>Texture émotionnelle</CardTitle><CardDescription>Émotions dominantes détectées {describeRange(summary)}</CardDescription></CardHeader><CardContent><ChartContainer className="aspect-auto h-[240px] w-full" config={emotionConfig} id="emotion-breakdown"><BarChart data={emotions} layout="vertical" margin={{ left: 8, right: 8 }}><CartesianGrid stroke="var(--border-soft)" horizontal={false} /><XAxis allowDecimals={false} type="number" /><YAxis axisLine={false} dataKey="label" tickLine={false} type="category" width={80} /><ChartTooltip content={<ChartTooltipContent />} /><Bar dataKey="count" fill="var(--color-count)" name="Messages" radius={[0, 4, 4, 0]}>{emotions.map((entry) => <Cell key={entry.emotion} fill={emotionColors[String(entry.emotion).toLowerCase()] || "var(--brand-orange)"} />)}</Bar></BarChart></ChartContainer></CardContent></Card><Card><CardHeader divider={false}><CardTitle>Évolution de la conversation</CardTitle><CardDescription>Volume des sentiments {describeRange(summary)}</CardDescription></CardHeader><CardContent><ChartContainer className="aspect-auto h-[300px] w-full" config={trendConfig} id="sentiment-trend"><AreaChart data={summary.trend} margin={{ left: 4, right: 8, top: 8, bottom: 0 }}><CartesianGrid stroke="var(--border-soft)" vertical={false} /><XAxis axisLine={false} dataKey="date" tickFormatter={(value) => new Date(value).toLocaleDateString("fr-FR", { weekday: "short" })} tickLine={false} /><YAxis axisLine={false} allowDecimals={false} tickLine={false} width={28} /><ChartTooltip content={<ChartTooltipContent />} /><Area dataKey="positive" fill="var(--color-positive)" fillOpacity={0.58} name="Positif" stackId="sentiment" stroke="var(--color-positive)" type="monotone" /><Area dataKey="neutral" fill="var(--color-neutral)" fillOpacity={0.42} name="Neutre" stackId="sentiment" stroke="var(--color-neutral)" type="monotone" /><Area dataKey="negative" fill="var(--color-negative)" fillOpacity={0.6} name="Négatif" stackId="sentiment" stroke="var(--color-negative)" type="monotone" /></AreaChart></ChartContainer></CardContent></Card></div>;
}

function MessagesTab({ messages, loading, query, label, onQueryChange, onLabelChange, onDeleteAll }: { messages: Message[]; loading: boolean; query: string; label: string; onQueryChange: (value: string) => void; onLabelChange: (value: string) => void; onDeleteAll: () => void }) {
  return <Card className="relative z-10 overflow-visible"><CardHeader divider={false}><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div><CardTitle>Flux des messages</CardTitle><CardDescription>Recherchez et filtrez les messages</CardDescription></div><div className="flex w-full flex-col gap-2 sm:w-auto sm:flex-row sm:items-center"><div className="w-full sm:min-w-64 sm:flex-1"><Input aria-label="Rechercher des messages" placeholder="Rechercher un texte…" value={query} onChange={(event) => onQueryChange(event.target.value)} /></div><SentimentSelect value={label} onChange={onLabelChange} /><ConfirmDialog confirmLabel="Supprimer définitivement" description="Tous les messages importés seront supprimés de la base de données. Cette action est irréversible." destructive onConfirm={onDeleteAll} title="Supprimer tous les messages ?" trigger={<Button iconStart={<Trash2 className="size-4" />} size="sm" tone="danger" variant="secondary">Tout supprimer</Button>} /></div></div></CardHeader><CardContent><div className="divide-y divide-border rounded-lg border border-border">{messages.length ? messages.slice(0, 100).map((message) => <div className="grid gap-3 p-4 lg:grid-cols-[120px_1fr_auto] lg:items-center" key={message.id}><time className="text-xs text-muted-foreground">{formatDate(message.timestamp)}</time><div className="min-w-0"><p className="mb-1 text-sm leading-6">{message.text}</p><p className="text-xs text-muted-foreground">{message.language || "Langue inconnue"} · {formatEmotion(message.emotion || "neutral")} · {message.summary || "Aucun résumé"}</p></div><div className="flex flex-wrap items-center justify-between gap-3 lg:justify-end"><SentimentBadge label={message.sentiment} /><span className="text-xs tabular-nums text-muted-foreground">{message.confidence ? `${Math.round(message.confidence * 100)} %` : "—"}</span></div></div>) : <div className="p-10 text-center text-sm text-muted-foreground">{loading ? "Chargement des messages…" : "Aucun message. Importez une conversation."}</div>}</div></CardContent></Card>;
}

function ImportTab({ importFile, importing, toolMessage, onFileChange, onImport }: { importFile: File | null; importing: boolean; toolMessage: string; onFileChange: (file: File | null) => void; onImport: () => Promise<void> }) {
  return <div className="w-full"><Card className="w-full"><CardHeader divider={false}><UploadCloud className="mb-1 size-5 text-[var(--brand-orange)]" /><CardTitle>Traiter une conversation WhatsApp</CardTitle><CardDescription>Choisissez un fichier de conversation ou une archive ZIP, puis classez-le avec le modèle local.</CardDescription></CardHeader><CardContent><div className="flex w-full flex-col gap-4"><label className="group flex min-h-52 w-full cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed border-[var(--brand-teal-action)] bg-[var(--brand-teal-soft)] px-6 py-8 text-center transition-colors hover:border-[var(--brand-orange)] hover:bg-[var(--brand-orange-soft)]"><input aria-label="Choisir une conversation WhatsApp" className="sr-only" type="file" onChange={(event) => onFileChange(event.target.files?.[0] || null)} /><span className="mb-3 grid size-12 place-items-center rounded-full bg-[var(--surface)] text-[var(--brand-teal-action)] shadow-sm transition-colors group-hover:text-[var(--brand-orange)]"><UploadCloud className="size-6" /></span><span className="text-sm font-medium">Déposez votre export WhatsApp ici</span><span className="mt-1 text-xs text-muted-foreground">ou cliquez pour choisir un fichier</span>{importFile && <span className="mt-3 rounded-full bg-[var(--surface)] px-3 py-1 text-xs text-muted-foreground">Fichier sélectionné : {importFile.name}</span>}</label><Button disabled={importing || !importFile} fullWidth onClick={() => void onImport()}>Importer et classer</Button>{toolMessage && <p className="text-sm text-[var(--danger)]">{toolMessage}</p>}</div></CardContent></Card></div>;
}

type LastImport = { fileName: string; created: number; from: string; to: string };

export default function Home() {
  const [activeTab, setActiveTab] = useState("home"); const [days, setDays] = useState(7); const [dateRange, setDateRange] = useState<DateRange | null>(null); const [summary, setSummary] = useState<Summary>(emptySummary); const [messages, setMessages] = useState<Message[]>([]); const [label, setLabel] = useState(""); const [query, setQuery] = useState(""); const [loading, setLoading] = useState(true); const [error, setError] = useState(""); const [importFile, setImportFile] = useState<File | null>(null); const [importing, setImporting] = useState(false); const [busyMessage, setBusyMessage] = useState(""); const [toolMessage, setToolMessage] = useState(""); const [lastImport, setLastImport] = useState<LastImport | null>(null);

  const refresh = useCallback(async () => { setLoading(true); setError(""); try { const period = dateRange ? { since: dateRange.from, until: dateRange.to } : { days }; const [nextSummary, nextMessages] = await Promise.all([getSummary(period), getMessages(label, query)]); setSummary(nextSummary); setMessages(nextMessages); } catch (reason) { setError(reason instanceof Error ? reason.message : "Impossible de charger les données du tableau de bord."); } finally { setLoading(false); } }, [days, dateRange, label, query]);
  useEffect(() => { void refresh(); }, [refresh]);
  async function handleImport() {
    if (!importFile) { setToolMessage("Choisissez d'abord un fichier de conversation."); return; }
    setImporting(true); setBusyMessage("L’IA analyse vos messages…"); setToolMessage("");
    try {
      const result = await importChat(importFile);
      const from = result.result.range.from.slice(0, 10);
      const to = result.result.range.to.slice(0, 10);
      setLastImport({ fileName: importFile.name, created: result.result.created, from, to });
      setDateRange({ from, to });
      setActiveTab("overview");
    } catch (reason) {
      setToolMessage(reason instanceof Error ? reason.message : "Échec de l'importation.");
    } finally {
      setImporting(false); setBusyMessage("");
    }
  }
  async function handleDeleteAll() {
    setBusyMessage("Suppression des messages…"); setError("");
    try {
      await deleteAllMessages();
      setLastImport(null);
      await refresh();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Impossible de supprimer les messages.");
    } finally {
      setBusyMessage("");
    }
  }
  // Le bandeau d'import n'est affiché que tant que la période consultée
  // correspond encore à celle de cet import : dès que l'utilisateur change
  // de période (prédéfinie ou personnalisée), l'affirmation « vous
  // consultez... » ne serait plus vraie, donc le bandeau doit disparaître de
  // lui-même et pas seulement sur un clic sur le bouton de fermeture.
  const showImportBanner = Boolean(lastImport && dateRange && dateRange.from === lastImport.from && dateRange.to === lastImport.to);
  return <main className="min-h-screen bg-background px-4 py-6 text-foreground sm:px-6 lg:px-8">{busyMessage && <div aria-live="polite" className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background/90 backdrop-blur-sm"><svg aria-hidden="true" className="size-10 animate-spin text-[var(--brand-orange)]" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" d="M4 12a8 8 0 0 1 8-8" stroke="currentColor" strokeLinecap="round" strokeWidth="4" /></svg><p className="text-sm font-medium text-foreground">{busyMessage}</p><p className="text-xs text-muted-foreground">Merci de patienter, ne fermez pas cette page.</p></div>}<div className="mx-auto flex min-h-[calc(100vh-3rem)] max-w-7xl flex-col gap-6"><section className="border-b border-border pb-6"><h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">Comprenez l'ambiance.</h1><p className="mt-3 max-w-2xl text-sm leading-6 text-muted-foreground">Découvrez comment votre groupe se sent, message par message et au fil du temps.</p></section>{error && <div className="rounded-lg border border-[var(--danger-soft)] bg-[var(--danger-soft)] p-3 text-sm text-[var(--danger)]">{error}</div>}{summary.alerts.map((alert) => <div className="flex items-center gap-3 rounded-lg border border-[var(--warning-soft)] bg-[var(--warning-soft)] p-3 text-sm text-[var(--warning-foreground)]" key={alert.kind}><strong>{alert.title}</strong><span>{alert.description}</span></div>)}<Tabs className="gap-5" onValueChange={setActiveTab} orientation="horizontal" value={activeTab}><ScrollableTabsList><TabsTrigger value="home"><UploadCloud className="size-4" />Accueil</TabsTrigger><TabsTrigger value="overview"><Gauge className="size-4" />Vue d’ensemble</TabsTrigger><TabsTrigger value="messages"><MessageSquareText className="size-4" />Messages</TabsTrigger></ScrollableTabsList>{showImportBanner && lastImport && <div className="flex flex-col gap-1 rounded-lg border border-[var(--success-soft)] bg-[var(--success-soft)] p-3 text-sm text-[var(--success-solid)]"><div className="flex items-start justify-between gap-3"><span className="font-medium">{lastImport.created} messages importés.</span><button aria-label="Fermer" className="text-xs text-[var(--success-solid)] opacity-70 hover:opacity-100" onClick={() => setLastImport(null)} type="button">✕</button></div><span className="text-xs opacity-80">Vous consultez la période du {formatShortDate(lastImport.from)} au {formatShortDate(lastImport.to)}, issue de « {lastImport.fileName} ».</span></div>}<TabsContent value="home"><ImportTab importFile={importFile} importing={importing} onFileChange={setImportFile} onImport={handleImport} toolMessage={toolMessage} /></TabsContent><TabsContent value="overview"><OverviewTab dateRange={dateRange} days={days} onClearRange={() => setDateRange(null)} onDaysChange={setDays} onRangeChange={setDateRange} summary={summary} /></TabsContent><TabsContent value="messages"><MessagesTab label={label} loading={loading} messages={messages} onDeleteAll={handleDeleteAll} onLabelChange={setLabel} onQueryChange={setQuery} query={query} /></TabsContent></Tabs><footer className="mt-auto flex flex-col justify-between gap-2 border-t border-border pt-5 text-xs text-muted-foreground sm:flex-row"><span>Prototype académique</span><span>Modèle local AfroXLMR-small</span></footer></div></main>;
}
