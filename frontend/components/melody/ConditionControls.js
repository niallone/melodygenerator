'use client';

const ConditionControls = ({
  conditions,
  keySignature,
  onKeyChange,
  tempo,
  onTempoChange,
  style,
  onStyleChange,
}) => {
  if (!conditions) return null;

  return (
    <div className="space-y-3">
      <h4 className="text-sm font-semibold">Conditions (optional)</h4>

      {/* Key Signature */}
      {conditions.keys && (
        <div>
          <label className="block text-sm mb-1">Key Signature</label>
          <select
            value={keySignature}
            onChange={(e) => onKeyChange(e.target.value)}
            className="w-full p-2 text-sm border border-primary rounded"
          >
            <option value="">Any</option>
            {conditions.keys.map((key) => (
              <option key={key} value={key}>
                {key}
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Tempo */}
      {conditions.tempos && (
        <div>
          <label className="block text-sm mb-1">
            Tempo: {tempo || 'Any'} {tempo ? 'BPM' : ''}
          </label>
          <select
            value={tempo}
            onChange={(e) => onTempoChange(e.target.value)}
            className="w-full p-2 text-sm border border-primary rounded"
          >
            <option value="">Any</option>
            {conditions.tempos.map((t) => (
              <option key={t} value={t}>
                {t} BPM
              </option>
            ))}
          </select>
        </div>
      )}

      {/* Style */}
      {conditions.styles && (
        <div>
          <label className="block text-sm mb-1">Style</label>
          <select
            value={style}
            onChange={(e) => onStyleChange(e.target.value)}
            className="w-full p-2 text-sm border border-primary rounded"
          >
            <option value="">Any</option>
            {conditions.styles.map((s) => (
              <option key={s} value={s}>
                {s.charAt(0).toUpperCase() + s.slice(1)}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
};

export default ConditionControls;
