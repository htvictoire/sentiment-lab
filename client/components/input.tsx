import * as React from "react";
import styles from "@/styles/ui.module.css";

type InputProps = Omit<React.ComponentProps<"input">, "className"> & {
  readonly errorMessage?: string | null;
};

function Input({ type, errorMessage, ...props }: InputProps) {
  const input = (
    <input
      className={`${styles.fieldControl} ${styles.fieldInput}`}
      data-slot="input"
      type={type}
      {...props}
      aria-invalid={errorMessage ? "true" : "false"}
    />
  );

  if (!errorMessage) {
    return input;
  }

  return (
    <div className={styles.fieldErrorWrap}>
      {input}
      <p className={styles.fieldErrorMessage}>{errorMessage}</p>
    </div>
  );
}

export { Input };
