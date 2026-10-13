<script setup>
import { onUnmounted, watch } from "vue";
import { ArrowRight, X } from "lucide-vue-next";
import { translate } from "../../utils/translation";

const props = defineProps({
	open: {
		type: Boolean,
		default: false,
	},
});

const emit = defineEmits(["close"]);

// Box colours per workflow state, matching the state pills of the panel.
const STATE_BOX = {
	draft: "fill-gray-50 stroke-gray-400 dark:fill-gray-800 dark:stroke-gray-500",
	analyze: "fill-blue-50 stroke-blue-500 dark:fill-blue-900/40 dark:stroke-blue-400",
	quoted: "fill-amber-50 stroke-amber-500 dark:fill-amber-900/30 dark:stroke-amber-400",
	accepted: "fill-green-50 stroke-green-600 dark:fill-green-900/30 dark:stroke-green-400",
	converted: "fill-violet-50 stroke-violet-500 dark:fill-violet-900/30 dark:stroke-violet-400",
	rejected: "fill-red-50 stroke-red-500 dark:fill-red-900/30 dark:stroke-red-400",
	neutral: "fill-white stroke-gray-300 dark:fill-gray-800 dark:stroke-gray-600",
};

// Customer Request workflow, drawn top to bottom (see the Customer Request
// Workflow in patches/post_model_sync/setup_customer_change_requests.py).
const CUSTOMER_REQUEST_BOXES = [
	{ x: 20, y: 10, tone: "draft", name: "Draft", desc: "the team writes the request down" },
	{ x: 20, y: 110, tone: "analyze", name: "To Analyze", desc: "queue: Take / Release" },
	{ x: 20, y: 210, tone: "quoted", name: "Quoted", desc: "quote sent to the customer" },
	{ x: 20, y: 310, tone: "accepted", name: "Accepted", desc: "the customer agreed" },
	{ x: 20, y: 410, tone: "converted", name: "Converted", desc: "change request created" },
	{ x: 400, y: 210, tone: "rejected", name: "Rejected", desc: "can go back to analysis" },
];

// Change Request workflow; "Approved" only lasts until the save that creates the task.
const CHANGE_REQUEST_BOXES = [
	{ x: 20, y: 10, tone: "draft", name: "Draft", desc: "created from an accepted request" },
	{ x: 20, y: 110, tone: "accepted", name: "Approved", desc: "lasts a moment", dashed: true },
	{ x: 20, y: 210, tone: "analyze", name: "Task Created", desc: "the task is in progress" },
	{ x: 20, y: 310, tone: "converted", name: "Done", desc: "work finished" },
	{ x: 400, y: 210, tone: "neutral", name: "Project task", desc: "status: Open" },
	{ x: 400, y: 310, tone: "rejected", name: "Cancelled", desc: "work dropped" },
];

const OVERVIEW_STEPS = [
	{ name: "Customer", desc: "meeting, email, call", tone: "border-gray-300 dark:border-gray-600" },
	{ name: "Customer Request", desc: "what the customer asks for", tone: "border-blue-400 dark:border-blue-500" },
	{ name: "Change Request", desc: "what we approved", tone: "border-violet-400 dark:border-violet-500" },
	{ name: "Project task", desc: "the team's work", tone: "border-green-500 dark:border-green-500" },
];
const OVERVIEW_LINKS = ["the team records it", "after acceptance", "on approval"];

function close() {
	emit("close");
}

// Captured on document so Escape closes only this modal, not the panels behind
// it that listen on window.
function handleEscape(event) {
	if (event.key !== "Escape") return;
	event.stopPropagation();
	close();
}

watch(
	() => props.open,
	(open) => {
		if (open) {
			document.addEventListener("keydown", handleEscape, true);
		} else {
			document.removeEventListener("keydown", handleEscape, true);
		}
	},
	{ immediate: true }
);

onUnmounted(() => {
	document.removeEventListener("keydown", handleEscape, true);
});
</script>

<template>
	<Teleport to="body">
		<div
			v-if="open"
			class="fixed inset-0 z-50 overflow-y-auto bg-gray-900/50 px-4 py-6"
			@click.self="close"
		>
			<div
				class="mx-auto flex w-full max-w-3xl flex-col overflow-hidden rounded-2xl bg-white dark:bg-gray-900 shadow-xl"
				role="dialog"
				aria-modal="true"
				aria-labelledby="requests-guide-title"
			>
				<div class="flex items-start justify-between gap-4 border-b border-gray-100 dark:border-gray-800 px-5 py-4">
					<div>
						<h3 id="requests-guide-title" class="text-lg font-semibold text-gray-900 dark:text-gray-100">
							{{ translate("How requests work") }}
						</h3>
						<p class="text-sm text-gray-500 dark:text-gray-400">
							{{ translate("team = Projects User, manager = Projects Manager") }}
						</p>
					</div>
					<button
						type="button"
						class="rounded-md p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 dark:hover:bg-gray-800 dark:hover:text-gray-200"
						:title="translate('Close')"
						@click="close"
					>
						<X class="h-5 w-5" />
					</button>
				</div>

				<div class="space-y-8 px-5 py-5 text-sm text-gray-700 dark:text-gray-300">
					<!-- Overview: request -> change request -> task -->
					<section class="space-y-3">
						<p>
							{{ translate("A customer request records what the customer asks for. Once the customer accepts the quote, it becomes a change request: what we approved. Approving the change request creates the task in the project.") }}
						</p>
						<div class="flex flex-col items-stretch gap-2 md:flex-row md:items-center">
							<template v-for="(step, index) in OVERVIEW_STEPS" :key="step.name">
								<div
									:class="[
										'min-w-0 flex-1 rounded-lg border-2 bg-white dark:bg-gray-800 px-3 py-2 text-center',
										step.tone,
									]"
								>
									<div class="font-semibold text-gray-900 dark:text-gray-100">{{ translate(step.name) }}</div>
									<div class="text-xs text-gray-500 dark:text-gray-400">{{ translate(step.desc) }}</div>
								</div>
								<div
									v-if="index < OVERVIEW_LINKS.length"
									class="flex flex-row items-center justify-center gap-1 text-xs text-gray-500 dark:text-gray-400 md:w-24 md:flex-col md:gap-0"
								>
									<ArrowRight class="h-4 w-4 rotate-90 md:rotate-0" />
									<span class="text-center">{{ translate(OVERVIEW_LINKS[index]) }}</span>
								</div>
							</template>
						</div>
					</section>

					<!-- Customer Request workflow -->
					<section class="space-y-3">
						<h4 class="text-base font-semibold text-gray-900 dark:text-gray-100">
							{{ translate("Customer request stages") }}
						</h4>
						<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 p-3">
							<svg
								viewBox="0 0 700 465"
								class="mx-auto block h-auto w-full min-w-[560px] max-w-[640px] text-gray-500 dark:text-gray-400"
								role="img"
								:aria-label="translate('Customer request stages: Draft, To Analyze, Quoted, Accepted and Converted. A request can be rejected during analysis or after the quote, and a rejected request can go back to analysis.')"
							>
								<defs>
									<marker id="guide-arrow-crq" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
										<path d="M0,0 L10,5 L0,10 z" fill="currentColor" />
									</marker>
								</defs>

								<g v-for="box in CUSTOMER_REQUEST_BOXES" :key="box.name">
									<rect :x="box.x" :y="box.y" width="200" height="44" rx="8" stroke-width="1.5" :class="STATE_BOX[box.tone]" />
									<text :x="box.x + 100" :y="box.y + 19" text-anchor="middle" class="fill-gray-900 dark:fill-gray-100 text-[13px] font-semibold">{{ translate(box.name) }}</text>
									<text :x="box.x + 100" :y="box.y + 35" text-anchor="middle" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate(box.desc) }}</text>
								</g>

								<g fill="none" stroke="currentColor" stroke-width="1.5">
									<line x1="120" y1="56" x2="120" y2="106" marker-end="url(#guide-arrow-crq)" />
									<line x1="120" y1="156" x2="120" y2="206" marker-end="url(#guide-arrow-crq)" />
									<line x1="120" y1="256" x2="120" y2="306" marker-end="url(#guide-arrow-crq)" />
									<line x1="120" y1="356" x2="120" y2="406" stroke-dasharray="6 5" marker-end="url(#guide-arrow-crq)" />
									<path d="M222 140 H470 V206" marker-end="url(#guide-arrow-crq)" />
									<path d="M222 232 H396" marker-end="url(#guide-arrow-crq)" />
									<path d="M560 208 V124 H226" marker-end="url(#guide-arrow-crq)" />
								</g>

								<g class="text-[12px]">
									<text x="134" y="78" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Submit for Analysis") }}</text>
									<text x="134" y="92" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("team") }}</text>

									<text x="134" y="170" class="fill-blue-600 dark:fill-blue-400 text-[11px] font-semibold">{{ translate("needs analysis and hours") }}</text>
									<text x="134" y="184" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Mark Quoted") }}</text>
									<text x="134" y="198" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager") }}</text>

									<text x="134" y="278" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Accept") }}</text>
									<text x="134" y="292" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager, after the customer decides") }}</text>

									<text x="134" y="378" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Create Change Request") }}</text>
									<text x="134" y="392" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager") }}</text>

									<text x="478" y="172" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Reject") }}</text>
									<text x="478" y="186" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager") }}</text>

									<text x="309" y="226" text-anchor="middle" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Reject") }}</text>
									<text x="309" y="248" text-anchor="middle" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager") }}</text>

									<text x="568" y="160" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Submit for Analysis") }}</text>
									<text x="568" y="174" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("team") }}</text>
								</g>
							</svg>
						</div>
						<ul class="list-disc space-y-1 pl-5">
							<li>{{ translate("To Analyze is a queue: anyone free takes a request with Take for analysis, or the manager assigns a developer in Desk.") }}</li>
							<li>{{ translate("The analysis and estimate are written in Desk (Analyze in Desk). A quotation can be linked once the request is quoted.") }}</li>
							<li>{{ translate("The dashed arrow is not a workflow step: Converted is set only when the change request is created, and copies the analysis, hours, amount and quotation.") }}</li>
						</ul>
					</section>

					<!-- Change Request workflow -->
					<section class="space-y-3">
						<h4 class="text-base font-semibold text-gray-900 dark:text-gray-100">
							{{ translate("Change request stages") }}
						</h4>
						<div class="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700 p-3">
							<svg
								viewBox="0 0 700 365"
								class="mx-auto block h-auto w-full min-w-[560px] max-w-[640px] text-gray-500 dark:text-gray-400"
								role="img"
								:aria-label="translate('Change request stages: Draft, Approved, Task Created, then Done or Cancelled. Approving creates the project task automatically.')"
							>
								<defs>
									<marker id="guide-arrow-chr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
										<path d="M0,0 L10,5 L0,10 z" fill="currentColor" />
									</marker>
								</defs>

								<g v-for="box in CHANGE_REQUEST_BOXES" :key="box.name">
									<rect
										:x="box.x"
										:y="box.y"
										width="200"
										height="44"
										rx="8"
										stroke-width="1.5"
										:stroke-dasharray="box.dashed ? '5 4' : null"
										:class="STATE_BOX[box.tone]"
									/>
									<text :x="box.x + 100" :y="box.y + 19" text-anchor="middle" class="fill-gray-900 dark:fill-gray-100 text-[13px] font-semibold">{{ translate(box.name) }}</text>
									<text :x="box.x + 100" :y="box.y + 35" text-anchor="middle" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate(box.desc) }}</text>
								</g>

								<g fill="none" stroke="currentColor" stroke-width="1.5">
									<line x1="120" y1="56" x2="120" y2="106" marker-end="url(#guide-arrow-chr)" />
									<line x1="120" y1="156" x2="120" y2="206" marker-end="url(#guide-arrow-chr)" />
									<line x1="120" y1="256" x2="120" y2="306" marker-end="url(#guide-arrow-chr)" />
									<path d="M222 232 H396" stroke-dasharray="6 5" marker-end="url(#guide-arrow-chr)" />
									<path d="M222 246 H300 V332 H396" marker-end="url(#guide-arrow-chr)" />
								</g>

								<g class="text-[12px]">
									<text x="134" y="78" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Approve") }}</text>
									<text x="134" y="92" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager") }}</text>

									<text x="134" y="184" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("automatically on save") }}</text>

									<text x="309" y="226" text-anchor="middle" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("creates") }}</text>

									<text x="134" y="278" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Mark Done") }}</text>
									<text x="134" y="292" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager") }}</text>

									<text x="308" y="290" class="fill-gray-900 dark:fill-gray-100 font-semibold">{{ translate("Cancel") }}</text>
									<text x="308" y="304" class="fill-gray-500 dark:fill-gray-400 text-[11px]">{{ translate("manager") }}</text>
								</g>
							</svg>
						</div>
						<ul class="list-disc space-y-1 pl-5">
							<li>{{ translate("Only the manager creates and approves change requests; the team can view them.") }}</li>
							<li>{{ translate("Approving creates the project task with the approved hours and scope.") }}</li>
							<li>{{ translate("Finishing the task does not close the change request: mark it done by hand.") }}</li>
						</ul>
					</section>
				</div>
			</div>
		</div>
	</Teleport>
</template>
