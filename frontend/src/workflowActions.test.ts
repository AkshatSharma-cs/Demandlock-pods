import { describe, expect, it } from "vitest";
import { buildModuleAttachmentPayload, buildOutcomePayload, buildPodEvaluationPayload, reviewAction } from "./workflowActions";

describe("cohort workflow", () => {
  it("builds pod-mode evaluation and published-module attachment requests", () => {
    expect(buildPodEvaluationPayload("block-1", "mobile_repair", "supervised_practice")).toEqual({
      block_code: "block-1", skill_family_id: "mobile_repair", pod_mode: "supervised_practice",
    });
    expect(buildModuleAttachmentPayload("module-1")).toEqual({ module_id: "module-1" });
  });
});

describe("review queue workflow", () => {
  it("allows adult employer review but blocks employer review of minors", () => {
    expect(reviewAction("employer", "18_plus")?.path).toBe("employer-review");
    expect(reviewAction("employer", "14_17")).toBeNull();
    expect(reviewAction("facilitator", "14_17")?.path).toBe("teacher-review");
  });
});

describe("outcomes workflow", () => {
  it("assigns verification level by actor role", () => {
    expect(buildOutcomePayload("student", "s", "p", "task_completed").verification_level).toBe("self_reported");
    expect(buildOutcomePayload("facilitator", "s", "p", "task_completed").verification_level).toBe("facilitator_confirmed");
    expect(buildOutcomePayload("employer", "s", "p", "started_work").verification_level).toBe("employer_confirmed");
  });
});
