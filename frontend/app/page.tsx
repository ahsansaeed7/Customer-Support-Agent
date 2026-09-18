"use client";

import { useEffect, useState, useCallback } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

type Booking = {
  id: string;
  booking_reference: string;
  status: string;
  phone_number: string;
  tour_title: string;
  travel_date: string;
  pax_count: number;
  total_amount: number;
  currency: string;
};

const STATUS_OPTIONS = [
  { value: "", label: "All" },
  { value: "draft", label: "Draft" },
  { value: "pending_payment", label: "Pending Payment" },
  { value: "confirmed", label: "Confirmed" },
  { value: "cancelled", label: "Cancelled" },
];

const STATUS_STYLES: Record<string, string> = {
  draft: "bg-gray-100 text-gray-700",
  pending_payment: "bg-yellow-100 text-yellow-800",
  confirmed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-700",
};

export default function DashboardPage() {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [approvingId, setApprovingId] = useState<string | null>(null);

  const fetchBookings = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const url = statusFilter
        ? `${API_URL}/dashboard/bookings?status=${statusFilter}`
        : `${API_URL}/dashboard/bookings`;
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Failed to fetch bookings (${res.status})`);
      const data = await res.json();
      setBookings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    fetchBookings();
  }, [fetchBookings]);

  async function handleApprove(bookingId: string) {
    setApprovingId(bookingId);
    try {
      const res = await fetch(`${API_URL}/dashboard/bookings/${bookingId}/approve`, {
        method: "POST",
      });
      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.detail || `Approval failed (${res.status})`);
      }
      await fetchBookings();
    } catch (err) {
      alert(err instanceof Error ? err.message : "Approval failed.");
    } finally {
      setApprovingId(null);
    }
  }

  return (
    <main className="min-h-screen bg-slate-50 p-8">
      <div className="mx-auto max-w-6xl">
        <h1 className="text-2xl font-semibold text-slate-900">Bookings Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">
          Review bookings and approve payments once verified.
        </p>

        <div className="mt-6 flex items-center gap-3">
          <label className="text-sm font-medium text-slate-700">Filter by status:</label>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm"
          >
            {STATUS_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>
                {opt.label}
              </option>
            ))}
          </select>
          <button
            onClick={fetchBookings}
            className="rounded-md border border-slate-300 px-3 py-1.5 text-sm text-slate-700 hover:bg-slate-100"
          >
            Refresh
          </button>
        </div>

        {error && (
          <div className="mt-4 rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="min-w-full divide-y divide-slate-200 text-sm">
            <thead className="bg-slate-50">
              <tr>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Reference</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Customer</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Tour</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Date</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Pax</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Amount</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Status</th>
                <th className="px-4 py-3 text-left font-medium text-slate-600">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-400">
                    Loading...
                  </td>
                </tr>
              ) : bookings.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-4 py-6 text-center text-slate-400">
                    No bookings found.
                  </td>
                </tr>
              ) : (
                bookings.map((b) => (
                  <tr key={b.id}>
                    <td className="px-4 py-3 font-medium text-slate-900">{b.booking_reference}</td>
                    <td className="px-4 py-3 text-slate-600">{b.phone_number}</td>
                    <td className="px-4 py-3 text-slate-600">{b.tour_title}</td>
                    <td className="px-4 py-3 text-slate-600">{b.travel_date}</td>
                    <td className="px-4 py-3 text-slate-600">{b.pax_count}</td>
                    <td className="px-4 py-3 text-slate-600">
                      {b.currency} {b.total_amount.toLocaleString()}
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLES[b.status] || "bg-gray-100 text-gray-700"}`}
                      >
                        {b.status}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {b.status === "pending_payment" ? (
                        <button
                          onClick={() => handleApprove(b.id)}
                          disabled={approvingId === b.id}
                          className="rounded-md bg-green-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-green-700 disabled:opacity-50"
                        >
                          {approvingId === b.id ? "Approving..." : "Approve"}
                        </button>
                      ) : (
                        <span className="text-xs text-slate-400">—</span>
                      )}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </main>
  );
}
