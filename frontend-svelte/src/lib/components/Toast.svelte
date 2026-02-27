<!--
  Toast.svelte — Global toast notification component
  Mount once at App root level. Reads from toast store.
-->
<script>
    import { getToasts, dismissToast } from "../services/toast.svelte.js";
    import {
        X,
        CheckCircle,
        AlertCircle,
        AlertTriangle,
        Info,
    } from "lucide-svelte";

    let toasts = $derived(getToasts());

    const icons = {
        success: CheckCircle,
        error: AlertCircle,
        warning: AlertTriangle,
        info: Info,
    };

    const styles = {
        success:
            "bg-emerald-50 dark:bg-emerald-900/30 border-emerald-200 dark:border-emerald-700 text-emerald-800 dark:text-emerald-200",
        error: "bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700 text-red-800 dark:text-red-200",
        warning:
            "bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-700 text-amber-800 dark:text-amber-200",
        info: "bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700 text-blue-800 dark:text-blue-200",
    };

    const iconStyles = {
        success: "text-emerald-500",
        error: "text-red-500",
        warning: "text-amber-500",
        info: "text-blue-500",
    };
</script>

{#if toasts.length > 0}
    <div class="toast-container">
        {#each toasts as toast (toast.id)}
            <div
                class="toast-item {styles[toast.type] || styles.info}"
                role="alert"
            >
                <div
                    class="toast-icon {iconStyles[toast.type] ||
                        iconStyles.info}"
                >
                    {#if toast.type === "success"}
                        <CheckCircle class="h-5 w-5" />
                    {:else if toast.type === "error"}
                        <AlertCircle class="h-5 w-5" />
                    {:else if toast.type === "warning"}
                        <AlertTriangle class="h-5 w-5" />
                    {:else}
                        <Info class="h-5 w-5" />
                    {/if}
                </div>
                <p class="toast-message">{toast.message}</p>
                <button
                    type="button"
                    class="toast-close"
                    onclick={() => dismissToast(toast.id)}
                    aria-label="Tutup"
                >
                    <X class="h-4 w-4" />
                </button>
            </div>
        {/each}
    </div>
{/if}

<style>
    .toast-container {
        position: fixed;
        bottom: 1.5rem;
        right: 1.5rem;
        z-index: 9999;
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        max-width: 24rem;
        width: calc(100vw - 3rem);
    }

    @media (max-width: 640px) {
        .toast-container {
            bottom: 1rem;
            right: 1rem;
            left: 1rem;
            max-width: none;
            width: auto;
        }
    }

    .toast-item {
        display: flex;
        align-items: flex-start;
        gap: 0.75rem;
        padding: 0.875rem 1rem;
        border: 1px solid;
        border-radius: 0.75rem;
        box-shadow:
            0 10px 25px -5px rgb(0 0 0 / 0.15),
            0 8px 10px -6px rgb(0 0 0 / 0.1);
        animation: slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        backdrop-filter: blur(8px);
    }

    .toast-icon {
        flex-shrink: 0;
        margin-top: 0.05rem;
    }

    .toast-message {
        flex: 1;
        font-size: 0.875rem;
        line-height: 1.4;
        margin: 0;
    }

    .toast-close {
        flex-shrink: 0;
        padding: 0.25rem;
        border-radius: 0.375rem;
        opacity: 0.5;
        transition: opacity 0.15s;
        cursor: pointer;
        background: none;
        border: none;
        color: inherit;
    }
    .toast-close:hover {
        opacity: 1;
    }

    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
</style>
