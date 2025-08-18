import React, { ButtonHTMLAttributes } from 'react';
import clsx from 'clsx';

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  className?: string;
};

export default function Button({ className, ...props }: ButtonProps) {
  return (
    <button
      type="button"
      className={clsx(
        'rounded-[var(--mxc-radius-sm)] bg-[var(--mxc-topbar-bg)] px-4 py-2 text-[var(--mxc-topbar-fg)] shadow-[var(--mxc-shadow-sm)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--mxc-topbar-bg)]',
        className
      )}
      {...props}
    />
  );
}
