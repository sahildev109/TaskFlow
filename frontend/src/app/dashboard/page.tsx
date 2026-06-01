"use client";
import { useState, useEffect, useCallback } from "react";
import { useRouter } from "next/navigation";
import toast from "react-hot-toast";
import { useAuth } from "@/hooks/useAuth";
import { tasksAPI } from "@/lib/api";
import {
  Zap, LogOut, Plus, Trash2, Pencil, Check, X, Search,
  Loader2, ChevronLeft, ChevronRight, Shield, User
} from "lucide-react";
import clsx from "clsx";

interface Task {
  id: string;
  title: string;
  description?: string;
  status: "todo" | "in_progress" | "done" | "archived";
  priority: "low" | "medium" | "high" | "urgent";
  due_date?: string;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  todo: "bg-gray-700 text-gray-300",
  in_progress: "bg-blue-500/20 text-blue-400",
  done: "bg-green-500/20 text-green-400",
  archived: "bg-gray-500/20 text-gray-500",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-700 text-gray-400",
  medium: "bg-yellow-500/20 text-yellow-400",
  high: "bg-orange-500/20 text-orange-400",
  urgent: "bg-red-500/20 text-red-400",
};

export default function DashboardPage() {
  const { user, loading: authLoading, logout, isAdmin } = useAuth();
  const router = useRouter();

  const [tasks, setTasks] = useState<Task[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [priorityFilter, setPriorityFilter] = useState("");

  // Create task form
  const [showCreate, setShowCreate] = useState(false);
  const [newTask, setNewTask] = useState({ title: "", description: "", priority: "medium", status: "todo" });
  const [creating, setCreating] = useState(false);

  // Edit task
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<Task>>({});

  useEffect(() => {
    if (!authLoading && !user) router.push("/login");
  }, [user, authLoading, router]);

  const fetchTasks = useCallback(async () => {
    setLoading(true);
    try {
      const { data } = await tasksAPI.list({
        page,
        page_size: 10,
        search: search || undefined,
        status: statusFilter || undefined,
        priority: priorityFilter || undefined,
      });
      setTasks(data.tasks);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch {
      toast.error("Failed to load tasks");
    } finally {
      setLoading(false);
    }
  }, [page, search, statusFilter, priorityFilter]);

  useEffect(() => { if (user) fetchTasks(); }, [user, fetchTasks]);

  const handleCreate = async () => {
    if (!newTask.title.trim()) return toast.error("Title is required");
    setCreating(true);
    try {
      await tasksAPI.create(newTask);
      toast.success("Task created");
      setNewTask({ title: "", description: "", priority: "medium", status: "todo" });
      setShowCreate(false);
      fetchTasks();
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to create task");
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (id: string) => {
    try {
      await tasksAPI.delete(id);
      toast.success("Task deleted");
      fetchTasks();
    } catch {
      toast.error("Failed to delete task");
    }
  };

  const handleUpdate = async (id: string) => {
    try {
      await tasksAPI.update(id, editData);
      toast.success("Task updated");
      setEditingId(null);
      fetchTasks();
    } catch {
      toast.error("Failed to update task");
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/login");
  };

  if (authLoading) return (
    <div className="min-h-screen flex items-center justify-center">
      <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
    </div>
  );

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <header className="border-b border-gray-800 bg-gray-900/50 sticky top-0 z-10 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-indigo-400" />
            <span className="font-bold text-white">TaskFlow</span>
          </div>
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 text-sm text-gray-400">
              {isAdmin ? <Shield className="w-3.5 h-3.5 text-yellow-400" /> : <User className="w-3.5 h-3.5" />}
              <span>{user?.username}</span>
              {isAdmin && <span className="badge bg-yellow-500/20 text-yellow-400">admin</span>}
            </div>
            <button onClick={handleLogout} className="btn-ghost flex items-center gap-1.5 text-sm py-1.5 px-3">
              <LogOut className="w-4 h-4" /> Sign out
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 py-8 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {["todo", "in_progress", "done", "urgent"].map((s) => {
            const count = s === "urgent"
              ? tasks.filter(t => t.priority === "urgent").length
              : tasks.filter(t => t.status === s).length;
            const label = s === "urgent" ? "Urgent" : s.replace("_", " ");
            return (
              <div key={s} className="card py-4 text-center">
                <div className="text-2xl font-bold text-white">{count}</div>
                <div className="text-xs text-gray-500 capitalize mt-1">{label}</div>
              </div>
            );
          })}
        </div>

        {/* Filters + Create */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
            <input
              className="input pl-9"
              placeholder="Search tasks..."
              value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }}
            />
          </div>
          <select className="input w-auto" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(1); }}>
            <option value="">All statuses</option>
            <option value="todo">Todo</option>
            <option value="in_progress">In Progress</option>
            <option value="done">Done</option>
          </select>
          <select className="input w-auto" value={priorityFilter} onChange={e => { setPriorityFilter(e.target.value); setPage(1); }}>
            <option value="">All priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="urgent">Urgent</option>
          </select>
          <button onClick={() => setShowCreate(true)} className="btn-primary flex items-center gap-1.5 whitespace-nowrap">
            <Plus className="w-4 h-4" /> New Task
          </button>
        </div>

        {/* Create Task Form */}
        {showCreate && (
          <div className="card space-y-4 border-indigo-500/30">
            <h3 className="font-semibold text-white">Create New Task</h3>
            <input className="input" placeholder="Task title *" value={newTask.title} onChange={e => setNewTask(p => ({ ...p, title: e.target.value }))} />
            <textarea className="input resize-none h-20" placeholder="Description (optional)" value={newTask.description} onChange={e => setNewTask(p => ({ ...p, description: e.target.value }))} />
            <div className="flex gap-3">
              <select className="input" value={newTask.priority} onChange={e => setNewTask(p => ({ ...p, priority: e.target.value }))}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
              <select className="input" value={newTask.status} onChange={e => setNewTask(p => ({ ...p, status: e.target.value }))}>
                <option value="todo">Todo</option>
                <option value="in_progress">In Progress</option>
                <option value="done">Done</option>
              </select>
            </div>
            <div className="flex gap-2">
              <button onClick={handleCreate} disabled={creating} className="btn-primary flex items-center gap-1.5">
                {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />} Create
              </button>
              <button onClick={() => setShowCreate(false)} className="btn-ghost flex items-center gap-1.5">
                <X className="w-4 h-4" /> Cancel
              </button>
            </div>
          </div>
        )}

        {/* Task List */}
        <div className="space-y-3">
          {loading ? (
            <div className="flex justify-center py-12"><Loader2 className="w-6 h-6 animate-spin text-gray-500" /></div>
          ) : tasks.length === 0 ? (
            <div className="text-center py-16 text-gray-500">
              <div className="text-4xl mb-3">✓</div>
              <p>No tasks found</p>
            </div>
          ) : tasks.map(task => (
            <div key={task.id} className="card hover:border-gray-700 transition-colors">
              {editingId === task.id ? (
                <div className="space-y-3">
                  <input className="input" value={editData.title ?? task.title} onChange={e => setEditData(p => ({ ...p, title: e.target.value }))} />
                  <div className="flex gap-2">
                    <select className="input" value={editData.status ?? task.status} onChange={e => setEditData(p => ({ ...p, status: e.target.value as Task["status"] }))}>
                      <option value="todo">Todo</option>
                      <option value="in_progress">In Progress</option>
                      <option value="done">Done</option>
                      <option value="archived">Archived</option>
                    </select>
                    <select className="input" value={editData.priority ?? task.priority} onChange={e => setEditData(p => ({ ...p, priority: e.target.value as Task["priority"] }))}>
                      <option value="low">Low</option>
                      <option value="medium">Medium</option>
                      <option value="high">High</option>
                      <option value="urgent">Urgent</option>
                    </select>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => handleUpdate(task.id)} className="btn-primary py-1.5 text-sm flex items-center gap-1"><Check className="w-3.5 h-3.5" /> Save</button>
                    <button onClick={() => setEditingId(null)} className="btn-ghost py-1.5 text-sm flex items-center gap-1"><X className="w-3.5 h-3.5" /> Cancel</button>
                  </div>
                </div>
              ) : (
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-white truncate">{task.title}</span>
                      <span className={clsx("badge", STATUS_COLORS[task.status])}>{task.status.replace("_", " ")}</span>
                      <span className={clsx("badge", PRIORITY_COLORS[task.priority])}>{task.priority}</span>
                    </div>
                    {task.description && (
                      <p className="text-sm text-gray-500 mt-1 truncate">{task.description}</p>
                    )}
                    <p className="text-xs text-gray-600 mt-1">{new Date(task.created_at).toLocaleDateString()}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <button onClick={() => { setEditingId(task.id); setEditData({}); }} className="p-1.5 text-gray-500 hover:text-gray-300 transition-colors rounded">
                      <Pencil className="w-4 h-4" />
                    </button>
                    <button onClick={() => handleDelete(task.id)} className="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between">
            <p className="text-sm text-gray-500">{total} tasks</p>
            <div className="flex items-center gap-2">
              <button onClick={() => setPage(p => p - 1)} disabled={page === 1} className="btn-ghost py-1.5 px-2 disabled:opacity-40">
                <ChevronLeft className="w-4 h-4" />
              </button>
              <span className="text-sm text-gray-400">Page {page} of {totalPages}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page === totalPages} className="btn-ghost py-1.5 px-2 disabled:opacity-40">
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
