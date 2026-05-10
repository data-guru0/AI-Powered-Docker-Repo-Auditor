import { Amplify } from "aws-amplify";
import {
  signIn,
  signOut,
  signUp,
  confirmSignUp,
  fetchAuthSession,
  getCurrentUser,
  resendSignUpCode,
} from "aws-amplify/auth";

export function configureAmplify() {
  Amplify.configure({
    Auth: {
      Cognito: {
        userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID!,
        userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID!,
        signUpVerificationMethod: "code",
      },
    },
  });
}

export interface AuthUser {
  userId: string;
  email: string;
}

export async function getAuthenticatedUser(): Promise<AuthUser | null> {
  try {
    const user = await getCurrentUser();
    const session = await fetchAuthSession();
    const claims = session.tokens?.idToken?.payload;
    return {
      userId: user.userId,
      email: (claims?.email as string) || "",
    };
  } catch {
    return null;
  }
}

export async function loginUser(email: string, password: string) {
  return signIn({ username: email, password });
}

export async function registerUser(email: string, password: string) {
  return signUp({
    username: email,
    password,
    options: { userAttributes: { email } },
  });
}

export async function confirmRegistration(email: string, code: string) {
  return confirmSignUp({ username: email, confirmationCode: code });
}

export async function resendConfirmationCode(email: string) {
  return resendSignUpCode({ username: email });
}

export async function logoutUser() {
  return signOut();
}

export async function getIdToken(): Promise<string | null> {
  try {
    const session = await fetchAuthSession();
    return session.tokens?.idToken?.toString() || null;
  } catch {
    return null;
  }
}
