import type { MessageKey } from "../i18n/catalogues";
import { Msg } from "../i18n/provider";
import styles from "./page.module.css";

const PILLARS: readonly { title: MessageKey; body: MessageKey }[] = [
  { title: "home.measureTitle", body: "home.measureBody" },
  { title: "home.trainTitle", body: "home.trainBody" },
  { title: "home.rehearseTitle", body: "home.rehearseBody" },
];

export default function HomePage() {
  return (
    <div className={styles.page}>
      <section className={styles.intro}>
        <p className={styles.eyebrow}>
          <Msg id="home.eyebrow" />
        </p>
        <h1 className={styles.title}>
          <Msg id="home.title" />
        </h1>
        <p className={styles.lead}>
          <Msg id="home.lead" />
        </p>
      </section>
      <ul className={styles.pillars}>
        {PILLARS.map(({ title, body }) => (
          <li key={title} className={styles.card}>
            <h2 className={styles.cardTitle}>
              <Msg id={title} />
            </h2>
            <p className={styles.cardBody}>
              <Msg id={body} />
            </p>
          </li>
        ))}
      </ul>
    </div>
  );
}
