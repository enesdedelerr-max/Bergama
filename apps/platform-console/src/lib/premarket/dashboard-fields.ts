/**
 * Known-field projections for public DashboardPresentationOutput records.
 * Unknown keys are skipped. No recursive JSON rendering.
 */

export type DashboardScoreComponentsProjection = {
  watchlist_rank: string | null;
  gap_magnitude: string | null;
  catalyst_presence: string | null;
};

export type DashboardRecordProjection = {
  sequence_index: number | null;
  score_record_id: string | null;
  instrument_key: string | null;
  local_symbol: string | null;
  score: string | null;
  components: DashboardScoreComponentsProjection | null;
  morning_briefing_policy_version_id: string | null;
  scoring_policy_version_id: string | null;
  scoring_weight_profile_id: string | null;
  scoring_as_of: string | null;
  watchlist_rank: number | null;
  watchlist_rule_id: string | null;
  gap_record_id: string | null;
  catalyst_source_identifiers: readonly string[];
};

function asRecord(value: unknown): Record<string, unknown> | null {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    return null;
  }
  return value as Record<string, unknown>;
}

function asString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function asNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function asDecimalString(value: unknown): string | null {
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  return null;
}

function projectComponents(
  value: unknown,
): DashboardScoreComponentsProjection | null {
  const record = asRecord(value);
  if (!record) {
    return null;
  }
  return {
    watchlist_rank: asDecimalString(record.watchlist_rank),
    gap_magnitude: asDecimalString(record.gap_magnitude),
    catalyst_presence: asDecimalString(record.catalyst_presence),
  };
}

export function projectDashboardRecord(
  value: unknown,
): DashboardRecordProjection | null {
  const record = asRecord(value);
  if (!record) {
    return null;
  }

  const catalystRaw = record.catalyst_source_identifiers;
  const catalyst_source_identifiers = Array.isArray(catalystRaw)
    ? catalystRaw.filter((item): item is string => typeof item === "string")
    : [];

  return {
    sequence_index: asNumber(record.sequence_index),
    score_record_id: asString(record.score_record_id),
    instrument_key: asString(record.instrument_key),
    local_symbol: asString(record.local_symbol),
    score: asDecimalString(record.score),
    components: projectComponents(record.components),
    morning_briefing_policy_version_id: asString(
      record.morning_briefing_policy_version_id,
    ),
    scoring_policy_version_id: asString(record.scoring_policy_version_id),
    scoring_weight_profile_id: asString(record.scoring_weight_profile_id),
    scoring_as_of: asString(record.scoring_as_of),
    watchlist_rank: asNumber(record.watchlist_rank),
    watchlist_rule_id: asString(record.watchlist_rule_id),
    gap_record_id: asString(record.gap_record_id),
    catalyst_source_identifiers,
  };
}

export function projectDashboardRecords(
  records: readonly unknown[] | undefined | null,
): DashboardRecordProjection[] {
  if (!records) {
    return [];
  }
  return records
    .map((item) => projectDashboardRecord(item))
    .filter((item): item is DashboardRecordProjection => item !== null);
}
