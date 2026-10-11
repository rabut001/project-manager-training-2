import { useEffect, useRef, useState } from "react";
import {
  CHOICES,
  imageUrl,
  isCorrect,
  type Choice,
  type Exam,
  type Question,
} from "./exam.ts";
import {
  loadProgress,
  saveProgress,
  type AnswerRecord,
  type Progress,
} from "./progress.ts";
import type { LinkClick } from "./route.ts";

type PracticeProps = {
  exam: Exam;
  listHref: string;
  onLinkClick: LinkClick;
};

function questionByNo(exam: Exam, no: number): Question {
  const question = exam.questions.find((item) => item.no === no);
  if (!question) {
    return exam.questions[0];
  }
  return question;
}

function statusLabel(answer: AnswerRecord | undefined, question: Question): string {
  if (!answer) {
    return "未選択";
  }
  if (!answer.confirmed) {
    return "選択済み、未確認";
  }
  return isCorrect(question, answer.choice) ? "正解" : "誤答";
}

function numberLabel(
  no: number,
  answer: AnswerRecord | undefined,
  question: Question,
  checked: boolean,
): string {
  const mark = checked ? "チェック済み、" : "";
  return `問${no}、${mark}${statusLabel(answer, question)}`;
}

type DialogKind = "clear" | "grade";

export function Practice({ exam, listHref, onLinkClick }: PracticeProps) {
  const questionNos = new Set(exam.questions.map((question) => question.no));
  const [progress, setProgress] = useState<Progress>(() =>
    loadProgress(exam.id, questionNos),
  );
  const [dialogKind, setDialogKind] = useState<DialogKind | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const imageScroll = useRef<HTMLDivElement>(null);
  const lower = useRef<HTMLDivElement>(null);
  const shownKind = useRef<DialogKind>("clear");
  const onKey = useRef<(event: KeyboardEvent) => void>(() => {});
  if (dialogKind) {
    shownKind.current = dialogKind;
  }

  const currentNo = questionNos.has(progress.currentNo)
    ? progress.currentNo
    : exam.questions[0].no;
  const question = questionByNo(exam, currentNo);
  const answer = progress.answers[question.no];
  const confirmed = answer?.confirmed ?? false;

  useEffect(() => {
    saveProgress(exam.id, progress);
  }, [exam.id, progress]);

  useEffect(() => {
    imageScroll.current?.scrollTo(0, 0);
    lower.current?.scrollTo(0, 0);
  }, [question.no]);

  useEffect(() => {
    const listener = (event: KeyboardEvent) => onKey.current(event);
    window.addEventListener("keydown", listener);
    return () => window.removeEventListener("keydown", listener);
  }, []);

  useEffect(() => {
    const element = dialog.current;
    if (!element) {
      return;
    }
    if (dialogKind && !element.open) {
      element.showModal();
    }
    if (!dialogKind && element.open) {
      element.close();
    }
  }, [dialogKind]);

  const draftCount = exam.questions.filter((item) => {
    const record = progress.answers[item.no];
    return record !== undefined && !record.confirmed;
  }).length;
  const confirmedQuestions = exam.questions.filter(
    (item) => progress.answers[item.no]?.confirmed,
  );
  const correctCount = confirmedQuestions.filter(
    (item) => isCorrect(item, progress.answers[item.no].choice),
  ).length;
  const score =
    confirmedQuestions.length === 0
      ? "—"
      : `${correctCount}/${confirmedQuestions.length}（${Math.round(
          (correctCount / confirmedQuestions.length) * 100,
        )}%）`;

  function select(choice: Choice) {
    if (confirmed) {
      return;
    }
    setProgress((current) => ({
      ...current,
      currentNo: question.no,
      answers: {
        ...current.answers,
        [question.no]: { choice, confirmed: false },
      },
    }));
  }

  function confirmAnswer() {
    if (!answer || answer.confirmed) {
      return;
    }
    setProgress((current) => ({
      ...current,
      answers: {
        ...current.answers,
        [question.no]: { choice: answer.choice, confirmed: true },
      },
    }));
  }

  function moveTo(no: number) {
    if (!questionNos.has(no)) {
      return;
    }
    setProgress((current) => ({ ...current, currentNo: no }));
  }

  function dismissDialog() {
    dialog.current?.close();
    setDialogKind(null);
  }

  function gradeDrafts() {
    dialog.current?.close();
    setProgress((current) => {
      const answers = { ...current.answers };
      for (const item of exam.questions) {
        const record = answers[item.no];
        if (record && !record.confirmed) {
          answers[item.no] = { choice: record.choice, confirmed: true };
        }
      }
      return { ...current, answers };
    });
    setDialogKind(null);
  }

  function toggleCheck() {
    setProgress((current) => {
      const checked = current.checked.includes(question.no)
        ? current.checked.filter((no) => no !== question.no)
        : [...current.checked, question.no];
      return { ...current, checked };
    });
  }

  function clearSession() {
    dialog.current?.close();
    setProgress((current) => ({
      currentNo: 1,
      answers: {},
      checked: current.checked,
    }));
    setDialogKind(null);
  }

  const firstNo = exam.questions[0].no;
  const lastNo = exam.questions[exam.questions.length - 1].no;

  // PC のキー操作。1〜4 でア〜エ、Enter で結果を確認、← → で前へ・次へ。
  onKey.current = (event: KeyboardEvent) => {
    if (
      dialogKind ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey ||
      event.isComposing
    ) {
      return;
    }
    const target = event.target instanceof HTMLElement ? event.target : null;
    const index = ["1", "2", "3", "4"].indexOf(event.key);
    if (index >= 0) {
      select(CHOICES[index]);
    } else if (event.key === "ArrowLeft" && question.no !== firstNo) {
      event.preventDefault();
      moveTo(question.no - 1);
    } else if (event.key === "ArrowRight" && question.no !== lastNo) {
      event.preventDefault();
      moveTo(question.no + 1);
    } else if (
      event.key === "Enter" &&
      answer &&
      !confirmed &&
      (target === null || target === document.body || target.closest(".choices"))
    ) {
      // ほかのボタンにフォーカスがあるときは、そのボタンの Enter に任せる。
      event.preventDefault();
      confirmAnswer();
    }
  };

  return (
    <div className="practice">
      <header className="top">
        <a
          className="back"
          href={listHref}
          onClick={(event) => onLinkClick(event, listHref)}
        >
          一覧へ戻る
        </a>
        <div className="heading">
          <h1>{exam.title}</h1>
          <p className="score">
            正解 <span>{score}</span>
          </p>
        </div>
        <nav className="numbers" aria-label="問題番号">
          {exam.questions.map((item) => {
            const itemAnswer = progress.answers[item.no];
            const classes = ["number"];
            if (item.no === question.no) {
              classes.push("current");
            }
            if (itemAnswer?.confirmed) {
              classes.push(
                isCorrect(item, itemAnswer.choice) ? "correct" : "incorrect",
              );
            } else if (itemAnswer) {
              classes.push("draft");
            }
            return (
              <button
                key={item.no}
                type="button"
                className={classes.join(" ")}
                aria-current={item.no === question.no ? "true" : undefined}
                aria-label={numberLabel(
                  item.no,
                  itemAnswer,
                  item,
                  progress.checked.includes(item.no),
                )}
                onClick={() => moveTo(item.no)}
              >
                <span>{item.no}</span>
                <span className="badges" aria-hidden="true">
                  {itemAnswer?.confirmed && (
                    <span className="mark">
                      {isCorrect(item, itemAnswer.choice) ? "○" : "×"}
                    </span>
                  )}
                  {progress.checked.includes(item.no) && (
                    <span className="flag">
                      <svg viewBox="0 0 16 16">
                        <path d="M2.6 8.2 6.4 12.2 13.4 3.8" />
                      </svg>
                    </span>
                  )}
                </span>
              </button>
            );
          })}
        </nav>
      </header>

      <div className="image-pane">
        <div className="check-row">
          <label className="check">
            <input
              type="checkbox"
              checked={progress.checked.includes(question.no)}
              aria-label={`問${question.no}をチェック`}
              onChange={toggleCheck}
            />
          </label>
        </div>
        <div className="image-scroll" ref={imageScroll}>
          <img src={imageUrl(question.image)} alt={`問${question.no}`} />
        </div>
      </div>

      <div className="lower" ref={lower}>
        <div className="choices" role="group" aria-label="選択肢">
          {CHOICES.map((choice, index) => (
            <button
              key={choice}
              type="button"
              aria-keyshortcuts={String(index + 1)}
              className={answer?.choice === choice ? "selected" : undefined}
              aria-pressed={answer?.choice === choice}
              disabled={confirmed}
              onClick={() => select(choice)}
            >
              {choice}
            </button>
          ))}
        </div>

        {confirmed && answer ? (
          <section className="result" aria-live="polite">
            <p className={isCorrect(question, answer.choice) ? "ok" : "ng"}>
              {isCorrect(question, answer.choice) ? "正解" : "不正解"}
            </p>
            <p>
              正答 <strong>{question.answer ?? "—"}</strong>
            </p>
            {question.answer === null && (
              <p>
                IPA の解答例の注記: {question.answerNote}
                どの肢を選んでも正解として数えます。
              </p>
            )}
            <p>{question.explanation}</p>
            <p className="note">IPA の公式解説ではない</p>
          </section>
        ) : (
          <button
            type="button"
            className="confirm"
            aria-keyshortcuts="Enter"
            disabled={!answer}
            onClick={confirmAnswer}
          >
            結果を確認
          </button>
        )}

        <div className="pager">
          <button
            type="button"
            aria-keyshortcuts="ArrowLeft"
            disabled={question.no === firstNo}
            onClick={() => moveTo(question.no - 1)}
          >
            前へ
          </button>
          <button
            type="button"
            aria-keyshortcuts="ArrowRight"
            disabled={question.no === lastNo}
            onClick={() => moveTo(question.no + 1)}
          >
            次へ
          </button>
        </div>

        <button
          type="button"
          className="grade"
          disabled={draftCount === 0}
          onClick={() => setDialogKind("grade")}
        >
          一括採点
        </button>

        <button
          type="button"
          className="clear"
          onClick={() => setDialogKind("clear")}
        >
          回答をすべてクリア
        </button>

        <footer>
          <p className="keys">キー操作: 1〜4 選択、Enter 確認、← → 前後の問</p>
          <p>
            出典:{" "}
            <a href="https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html">
              IPA の過去問題
            </a>
          </p>
        </footer>
      </div>

      <dialog
        ref={dialog}
        onClose={() => setDialogKind(null)}
        aria-labelledby="dialog-title"
      >
        {shownKind.current === "grade" ? (
          <>
            <h2 id="dialog-title">選択済みの問をまとめて採点します</h2>
            <p>
              選択済みで未確認の{draftCount}問を確認済みにします。採点後は、その問の選択を変えられません。未選択の問は採点しません。
            </p>
            <div className="dialog-actions">
              <button type="button" onClick={dismissDialog}>
                中止
              </button>
              <button type="button" onClick={gradeDrafts}>
                採点する
              </button>
            </div>
          </>
        ) : (
          <>
            <h2 id="dialog-title">この回の解答を消します</h2>
            <p>
              {exam.title}の確認済みの解答と、まだ確認していない選択を消して、問1に戻ります。チェックはそのまま残します。
            </p>
            <div className="dialog-actions">
              <button type="button" onClick={dismissDialog}>
                中止
              </button>
              <button type="button" className="danger" onClick={clearSession}>
                消してやり直す
              </button>
            </div>
          </>
        )}
      </dialog>
    </div>
  );
}
