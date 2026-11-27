import { Msg } from "../i18n/provider";
import { Button } from "../components/Button";
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
      <Button href="/">
        <Msg id="shell.notFoundHome" />
      </Button>
    </div>
  );
}
