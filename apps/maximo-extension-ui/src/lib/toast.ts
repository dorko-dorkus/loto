export function toastError(message: string): void {
  if (typeof window !== 'undefined' && typeof window.alert === 'function') {
    try {
      window.alert(message);
    } catch {
      /* ignore environments without alert */
    }
  }
  console.error(message);
}
