import NextAuth, { type NextAuthOptions } from "next-auth";
import type { JWT } from "next-auth/jwt";
import CredentialsProvider from "next-auth/providers/credentials";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "";

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      name: "Email",
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      async authorize(credentials) {
        if (!credentials?.email || !credentials.password) {
          throw new Error("Enter both email and password");
        }
        const response = await fetch(`${API_BASE.replace(/\/$/, "")}/api/auth/login`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            email: credentials.email,
            password: credentials.password,
          }),
        });

        if (!response.ok) {
          const text = await response.text();
          throw new Error(text || "Invalid login");
        }

        const data = await response.json();
        return {
          id: data.user?.id ?? credentials.email,
          name: data.user?.name ?? credentials.email,
          email: data.user?.email ?? credentials.email,
        };
      },
    }),
  ],
  session: {
    strategy: "jwt",
  },
  pages: {
    signIn: "/login",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user && typeof user === "object") {
        const typedUser = user as { id?: string };
        if (typedUser.id) {
          (token as JWT & { id?: string }).id = typedUser.id;
        }
      }
      return token;
    },
    async session({ session, token }) {
      const typedToken = token as JWT & { id?: string };
      if (session.user && typedToken.id) {
        (session.user as { id?: string }).id = typedToken.id;
      }
      return session;
    },
  },
  secret: process.env.AUTH_SECRET,
};

export default NextAuth(authOptions);
