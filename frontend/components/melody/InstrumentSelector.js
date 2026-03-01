'use client';

const InstrumentSelector = ({ instruments, selectedInstrument, onSelectInstrument }) => {
  if (instruments.length === 0) {
    return <div className="mb-4">No instruments available</div>;
  }

  return (
    <div className="mb-4">
      <select
        value={selectedInstrument}
        onChange={(e) => onSelectInstrument(Number(e.target.value))}
        className="w-full p-2 text-base border border-primary rounded"
      >
        {instruments.map((inst) => (
          <option key={inst.id} value={inst.id}>
            {inst.name}
          </option>
        ))}
      </select>
    </div>
  );
};

export default InstrumentSelector;
