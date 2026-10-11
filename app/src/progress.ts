import { CHOICES, type Choice } from "./exam.ts";

export type AnswerRecord = {
  choice: Choice;
  confirmed: boolean;
};

export type Progress = {
  currentNo: number;
  answers: Record<number, AnswerRecord>;
  checked: number[];
};

export function storageKey(examId: string): string {
  return `pm-am2:${examId}`;
}

export function emptyProgress(): Progress {
  return { currentNo: 1, answers: {}, checked: [] };
}

function sortedChecked(values: Iterable<number>): number[] {
  return [...new Set(values)].sort((left, right) => left - right);
}

function readChecked(value: unknown, questionNos: ReadonlySet<number>): number[] {
  if (!Array.isArray(value)) {
    return [];
  }
  const seen: number[] = [];
  for (const item of value) {
    if (typeof item === "number" && Number.isInteger(item) && questionNos.has(item)) {
      seen.push(item);
    }
  }
  return sortedChecked(seen);
}

function isAnswer(value: unknown): value is AnswerRecord {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const answer = value as Record<string, unknown>;
  return (
    typeof answer.choice === "string" &&
    CHOICES.includes(answer.choice as Choice) &&
    typeof answer.confirmed === "boolean"
  );
}

export function loadProgress(
  examId: string,
  questionNos: ReadonlySet<number>,
): Progress {
  const raw = localStorage.getItem(storageKey(examId));
  if (raw === null) {
    return emptyProgress();
  }
  try {
    const parsed = JSON.parse(raw) as Record<string, unknown>;
    const currentNo =
      typeof parsed.currentNo === "number" ? parsed.currentNo : 1;
    const answers: Record<number, AnswerRecord> = {};
    if (typeof parsed.answers === "object" && parsed.answers !== null) {
      for (const [no, answer] of Object.entries(parsed.answers)) {
        const questionNo = Number(no);
        if (Number.isInteger(questionNo) && isAnswer(answer)) {
          answers[questionNo] = answer;
        }
      }
    }
    return {
      currentNo,
      answers,
      checked: readChecked(parsed.checked, questionNos),
    };
  } catch {
    return emptyProgress();
  }
}

export function saveProgress(examId: string, progress: Progress): void {
  const stored: Progress = {
    ...progress,
    checked: sortedChecked(progress.checked),
  };
  localStorage.setItem(storageKey(examId), JSON.stringify(stored));
}

export function clearProgress(examId: string): void {
  localStorage.removeItem(storageKey(examId));
}
