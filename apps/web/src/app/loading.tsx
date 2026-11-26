import { Msg } from "../i18n/provider";
import styles from "./status.module.css";

export default function Loading() {
  return (
    <div className={styles.status} role="status">
      <span className={styles.spinner} aria-hidden="true" />
      <p className={styles.body}>
        <Msg id="shell.loading" />
      </p>
    </div>
  );
}
