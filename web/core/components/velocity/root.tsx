import { useState, useEffect, FC } from "react";
import { observer } from "mobx-react";
import { Controller, useForm } from "react-hook-form";
// ui
import { Button, Input, CustomSelect, TOAST_TYPE, setToast } from "@plane/ui";
// hooks
import { useProject } from "@/hooks/store";

// types
type VelocityFormValues = {
  initial_velocity: number;
  default_cycle_length: number;
  velocity_strategy: number;
};

const CYCLE_LENGTH_OPTIONS = [
  { value: 1, label: "1 Week" },
  { value: 2, label: "2 Weeks" },
  { value: 3, label: "3 Weeks" },
  { value: 4, label: "4 Weeks" },
];

const VELOCITY_STRATEGY_OPTIONS = [
  { value: 1, label: "1 Cycle" },
  { value: 2, label: "2 Cycles" },
  { value: 3, label: "3 Cycles" },
  { value: 4, label: "4 Cycles" },
];

type TVelocityRoot = {
  workspaceSlug: string;
  projectId: string;
  isAdmin: boolean;
};

export const VelocityRoot: FC<TVelocityRoot> = observer((props) => {
  const { workspaceSlug, projectId, isAdmin } = props;
  // states
  const [isSubmitting, setIsSubmitting] = useState(false);

  // store hooks
  const { currentProjectDetails, updateProject } = useProject();

  // form
  const {
    register,
    handleSubmit,
    formState: { errors, isDirty },
    reset,
    control,
  } = useForm<VelocityFormValues>({
    defaultValues: {
      initial_velocity: 10,
      default_cycle_length: 1,
      velocity_strategy: 3,
    },
  });

  useEffect(() => {
    if (currentProjectDetails) {
      // Ensure we're using the correct property names and getting number values
      const initialVelocity = typeof currentProjectDetails.initial_velocity === 'number'
        ? currentProjectDetails.initial_velocity
        : 10;

      const defaultCycleLength = typeof currentProjectDetails.default_cycle_length === 'number'
        ? currentProjectDetails.default_cycle_length
        : 1;

      const velocityStrategy = typeof currentProjectDetails.velocity_strategy === 'number'
        ? currentProjectDetails.velocity_strategy
        : 3;

      reset({
        initial_velocity: initialVelocity,
        default_cycle_length: defaultCycleLength,
        velocity_strategy: velocityStrategy,
      });
    }
  }, [currentProjectDetails, reset]);

  const onSubmit = async (data: VelocityFormValues) => {
    if (!workspaceSlug || !projectId || !currentProjectDetails) return;

    setIsSubmitting(true);

    try {
      console.log("Submitting velocity data:", data);

      // Ensure data values are numbers
      const payload = {
        initial_velocity: Number(data.initial_velocity),
        default_cycle_length: Number(data.default_cycle_length),
        velocity_strategy: Number(data.velocity_strategy)
      };

      await updateProject(workspaceSlug, projectId, payload);
      reset(data);
      setToast({
        type: TOAST_TYPE.SUCCESS,
        title: "Success!",
        message: "Velocity settings updated successfully.",
      });
    } catch (error) {
      console.error("Error updating velocity settings:", error);
      setToast({
        type: TOAST_TYPE.ERROR,
        title: "Error!",
        message: "Failed to update velocity settings. Please try again.",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="container mx-auto">
      <div className="space-y-2">
        {/* header */}
        <div className="flex flex-col items-start border-b border-custom-border-100 pb-3.5">
          <h3 className="text-xl font-medium leading-normal">Velocity Settings</h3>
        </div>

        <div className="space-y-5">
          <p className="text-sm text-custom-text-200">
            Configure velocity-related settings to accurately calculate project velocity.
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-8">
            <div className="space-y-5 divide-y divide-custom-border-200">
              <div className="flex flex-col gap-1">
                <h5 className="font-medium">Initial Velocity</h5>
                <p className="text-sm text-custom-text-300">Default velocity used for new projects and calculations.</p>
                <div className="mt-2 w-full sm:max-w-[240px]">
                  <Controller
                    name="initial_velocity"
                    control={control}
                    rules={{
                      required: "Initial velocity is required",
                      min: {
                        value: 0,
                        message: "Initial velocity must be a positive number",
                      },
                      validate: {
                        isNumber: value => !isNaN(Number(value)) || "Please enter a valid number",
                      }
                    }}
                    render={({ field: { onChange, value, ref } }) => (
                      <Input
                        id="initial_velocity"
                        name="initial_velocity"
                        type="number"
                        step="0.1" // Allow decimal values
                        placeholder="Enter initial velocity"
                        autoComplete="off"
                        error={errors.initial_velocity}
                        value={value?.toString()}
                        onChange={(e) => {
                          // Handle input as string to preserve decimal values
                          const inputValue = e.target.value;
                          const numValue = parseFloat(inputValue);

                          // Don't convert empty string to 0
                          if (inputValue === "") {
                            onChange("");
                          } else if (!isNaN(numValue)) {
                            onChange(numValue);
                          }
                        }}
                        ref={ref}
                        min={0}
                        disabled={!isAdmin}
                      />
                    )}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1 pt-5">
                <h5 className="font-medium">Default Cycle Length</h5>
                <p className="text-sm text-custom-text-300">
                  Default length of cycles for velocity calculations and planning.
                </p>
                <div className="mt-2 w-full sm:max-w-[240px]">
                  <Controller
                    name="default_cycle_length"
                    control={control}
                    render={({ field: { value, onChange } }) => (
                      <CustomSelect
                        value={value}
                        onChange={onChange}
                        label={CYCLE_LENGTH_OPTIONS.find((option) => option.value === value)?.label}
                        optionsClassName="w-full"
                        disabled={!isAdmin}
                      >
                        {CYCLE_LENGTH_OPTIONS.map((option) => (
                          <CustomSelect.Option key={option.value} value={option.value}>
                            {option.label}
                          </CustomSelect.Option>
                        ))}
                      </CustomSelect>
                    )}
                  />
                </div>
              </div>

              <div className="flex flex-col gap-1 pt-5">
                <h5 className="font-medium">Velocity Strategy</h5>
                <p className="text-sm text-custom-text-300">
                  Number of past cycles to consider when calculating project velocity.
                </p>
                <div className="mt-2 w-full sm:max-w-[240px]">
                  <Controller
                    name="velocity_strategy"
                    control={control}
                    render={({ field: { value, onChange } }) => (
                      <CustomSelect
                        value={value}
                        onChange={onChange}
                        label={VELOCITY_STRATEGY_OPTIONS.find((option) => option.value === value)?.label}
                        optionsClassName="w-full"
                        disabled={!isAdmin}
                      >
                        {VELOCITY_STRATEGY_OPTIONS.map((option) => (
                          <CustomSelect.Option key={option.value} value={option.value}>
                            {option.label}
                          </CustomSelect.Option>
                        ))}
                      </CustomSelect>
                    )}
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end">
              <Button
                type="submit"
                variant="primary"
                loading={isSubmitting}
                disabled={!isDirty || isSubmitting || !isAdmin}
              >
                {isSubmitting ? "Updating..." : "Update settings"}
              </Button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
});
