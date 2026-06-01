"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useForm } from "react-hook-form";
import toast from "react-hot-toast";
import { authAPI } from "@/lib/api";
import { useAuth } from "@/hooks/useAuth";
import { Loader2, Zap } from "lucide-react";

interface RegisterForm {
  full_name: string;
  email: string;
  username: string;
  password: string;
}

export default function RegisterPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm<RegisterForm>();

  const onSubmit = async (data: RegisterForm) => {
    setLoading(true);
    try {
      await authAPI.register(data);
      await login(data.email, data.password);
      toast.success("Account created!");
      router.push("/dashboard");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Registration failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-md space-y-8">
        <div className="text-center">
          <div className="flex items-center justify-center gap-2 mb-4">
            <Zap className="w-8 h-8 text-indigo-400" />
            <span className="text-2xl font-bold text-white">TaskFlow</span>
          </div>
          <h1 className="text-3xl font-bold text-white">Create account</h1>
          <p className="mt-2 text-gray-400">Start managing your tasks today</p>
        </div>

        <div className="card">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Full Name</label>
              <input className="input" placeholder="John Doe" {...register("full_name")} />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Email</label>
              <input
                type="email"
                className="input"
                placeholder="you@example.com"
                {...register("email", { required: "Email is required" })}
              />
              {errors.email && <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Username</label>
              <input
                className="input"
                placeholder="johndoe"
                {...register("username", {
                  required: "Username is required",
                  pattern: { value: /^[a-zA-Z0-9_]{3,50}$/, message: "3-50 chars, letters/numbers/underscores" },
                })}
              />
              {errors.username && <p className="mt-1 text-sm text-red-400">{errors.username.message}</p>}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">Password</label>
              <input
                type="password"
                className="input"
                placeholder="Min 8 chars, 1 uppercase, 1 digit"
                {...register("password", {
                  required: "Password is required",
                  minLength: { value: 8, message: "At least 8 characters" },
                })}
              />
              {errors.password && <p className="mt-1 text-sm text-red-400">{errors.password.message}</p>}
            </div>

            <button type="submit" disabled={loading} className="btn-primary w-full flex items-center justify-center gap-2 py-2.5">
              {loading ? <><Loader2 className="w-4 h-4 animate-spin" /> Creating...</> : "Create account"}
            </button>
          </form>
        </div>

        <p className="text-center text-gray-400 text-sm">
          Already have an account?{" "}
          <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
