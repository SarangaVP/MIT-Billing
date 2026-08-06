interface Props {
  title: string;
  message: string;
  confirmLabel?: string;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmPanel({ title, message, confirmLabel = "Delete", onConfirm, onCancel }: Props) {
  return (
    <div className="panel-overlay" onClick={onCancel}>
      <div className="panel panel-small" onClick={(e) => e.stopPropagation()}>
        <h2>{title}</h2>
        <p className="field-hint">{message}</p>

        <div className="panel-actions">
          <button type="button" className="btn btn-ghost" onClick={onCancel}>
            Cancel
          </button>
          <button
            type="button"
            className="btn btn-primary"
            style={{ background: "var(--danger)", borderColor: "var(--danger)" }}
            onClick={onConfirm}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}