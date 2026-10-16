export type WorkflowRole = "student" | "employer" | "facilitator" | "admin" | string;

export function buildPodEvaluationPayload(blockCode: string, skillFamilyId: string, podMode: string) {
  return { block_code: blockCode, skill_family_id: skillFamilyId, pod_mode: podMode };
}

export function buildModuleAttachmentPayload(moduleId: string) {
  return { module_id: moduleId };
}

export function reviewAction(role: WorkflowRole, ageBand: string) {
  if (ageBand !== "18_plus" && role === "employer") return null;
  return role === "employer"
    ? { path: "employer-review", body: { decision: "accepted", employer_feedback: "" } }
    : { path: "teacher-review", body: { rubric_scores: { safety: 3 }, teacher_feedback: "Reviewed against the practical rubric.", decision: "teacher_reviewed" } };
}

export function buildOutcomePayload(
  role: WorkflowRole,
  studentId: string,
  podId: string,
  stage: string,
  notes = "",
) {
  return {
    student_id: studentId,
    pod_id: podId,
    stage,
    verification_level: role === "student" ? "self_reported" : role === "employer" ? "employer_confirmed" : "facilitator_confirmed",
    notes,
  };
}
