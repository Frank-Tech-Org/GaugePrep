import { Msg } from "../i18n/provider";
import styles from "./status.module.css";

export default function NotFound() {
  return (
    <div className={styles.status}>
      <h1 className={styles.title}>
        <Msg id="shell.notFoundTitle" />
      </h1>
      <p className={styles.body}>
        <Msg id="shell.notFoundBody" />
      </p>
      <a className={styles.action} href="/">
        <Msg id="shell.notFoundHome" />
      </a>
    </div>
  );
}
