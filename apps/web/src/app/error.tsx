"use client";

import { Msg } from "../i18n/provider";
import { Button } from "../components/Button";
import styles from "./status.module.css";

export default function ErrorPage({ reset }: { reset: () => void }) {
  return (
    <div className={styles.status} role="alert">
      <h1 className={styles.title}>
        <Msg id="shell.errorTitle" />
      </h1>
      <p className={styles.body}>
        <Msg id="shell.errorBody" />
      </p>
      <Button onClick={reset}>
        <Msg id="shell.errorRetry" />
      </Button>
    </div>
  );
}
