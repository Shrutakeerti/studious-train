export function Spinner() {
  return <span className="spinner" aria-label="Loading" role="status" />;
}

export function ErrorBanner({ message, onRetry }) {
  if (!message) return null;
  return (
    <div className="banner banner-error" role="alert">
      <span>⚠</span>
      <div>
        <div>{message}</div>
        {onRetry && (
          <button
            className="btn btn-ghost"
            style={{ marginTop: 8, padding: "6px 12px" }}
            onClick={onRetry}
          >
            Try again
          </button>
        )}
      </div>
    </div>
  );
}

export function InfoBanner({ message }) {
  if (!message) return null;
  return (
    <div className="banner banner-info">
      <span>ℹ</span>
      <div>{message}</div>
    </div>
  );
}

export function StatusStamp({ status }) {
  const labels = {
    pending: "Pending",
    running: "Researching",
    completed: "Completed",
    failed: "Failed",
  };
  return (
    <span className={`stamp stamp-${status}`}>
      {labels[status] || status}
    </span>
  );
}
