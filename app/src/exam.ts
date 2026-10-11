export const CHOICES = ["ア", "イ", "ウ", "エ"] as const;

export type Choice = (typeof CHOICES)[number];

export type Question = {
  no: number;
  answer: Choice;
  image: string;
  explanation: string;
};

export type Exam = {
  id: string;
  title: string;
  questions: Question[];
};

export type ExamSummary = {
  id: string;
  title: string;
};

export class MissingExamError extends Error {}

const EXAM_ID = /^[0-9a-z-]+$/;

export function isExamId(value: string): boolean {
  return EXAM_ID.test(value);
}

function isChoice(value: unknown): value is Choice {
  return typeof value === "string" && CHOICES.includes(value as Choice);
}

function isQuestion(value: unknown): value is Question {
  if (typeof value !== "object" || value === null) {
    return false;
  }
  const question = value as Record<string, unknown>;
  return (
    typeof question.no === "number" &&
    isChoice(question.answer) &&
    typeof question.image === "string" &&
    typeof question.explanation === "string"
  );
}

export function parseExam(value: unknown): Exam {
  if (typeof value !== "object" || value === null) {
    throw new Error("問題データの形式が不正です。");
  }
  const exam = value as Record<string, unknown>;
  if (
    typeof exam.id !== "string" ||
    typeof exam.title !== "string" ||
    !Array.isArray(exam.questions) ||
    exam.questions.length === 0 ||
    !exam.questions.every(isQuestion)
  ) {
    throw new Error("問題データの形式が不正です。");
  }
  return {
    id: exam.id,
    title: exam.title,
    questions: exam.questions,
  };
}

function parseIndex(value: unknown): ExamSummary[] {
  if (
    !Array.isArray(value) ||
    !value.every(
      (item) =>
        typeof item === "object" &&
        item !== null &&
        typeof item.id === "string" &&
        typeof item.title === "string",
    )
  ) {
    throw new Error("回の一覧の形式が不正です。");
  }
  return value.map((item) => ({ id: item.id, title: item.title }));
}

function contentUrl(path: string): string {
  return `${import.meta.env.BASE_URL}content/${path}`;
}

function cached<T>(load: (key: string) => Promise<T>) {
  const pending = new Map<string, Promise<T>>();
  const resolved = new Map<string, T>();
  return {
    peek: (key: string) => resolved.get(key),
    load: (key: string) => {
      const existing = pending.get(key);
      if (existing) {
        return existing;
      }
      const promise = load(key)
        .then((value) => {
          resolved.set(key, value);
          return value;
        })
        .catch((error: unknown) => {
          pending.delete(key);
          throw error;
        });
      pending.set(key, promise);
      return promise;
    },
  };
}

const exams = cached(async (examId) => {
  const response = await fetch(contentUrl(`${examId}/exam.json`));
  if (response.status === 404) {
    throw new MissingExamError();
  }
  if (!response.ok) {
    throw new Error("問題データを読み込めませんでした。");
  }
  // 存在しないパスに 404.html（このアプリ）が返る環境では、JSON として読めない。
  const exam = parseExam(await response.json().catch(() => {
    throw new MissingExamError();
  }));
  if (exam.id !== examId) {
    throw new Error("問題データの id が一致しません。");
  }
  return exam;
});

const indexes = cached(async () => {
  const response = await fetch(contentUrl("index.json"));
  if (!response.ok) {
    throw new Error("回の一覧を読み込めませんでした。");
  }
  return parseIndex(await response.json());
});

export const peekExam = exams.peek;
export const loadExam = exams.load;
export const peekIndex = () => indexes.peek("index");
export const loadIndex = () => indexes.load("index");

export function imageUrl(image: string): string {
  return contentUrl(image);
}
