export default function Page() {
  return (
    <main>
      <h1 className="mb-4 text-xl font-semibold">Portfolio</h1>
      <table className="min-w-full border border-[var(--mxc-border)]">
        <thead className="bg-[var(--mxc-nav-bg)] text-left">
          <tr>
            <th className="px-4 py-2">Name</th>
            <th className="px-4 py-2">Status</th>
            <th className="px-4 py-2">Owner</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td className="px-4 py-6 text-center" colSpan={3}>
              No data
            </td>
          </tr>
        </tbody>
      </table>
    </main>
  );
}
