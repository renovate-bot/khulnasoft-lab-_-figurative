import glob
import threading
import time
import unittest
from inspect import currentframe, getframeinfo
from pathlib import Path
from shutil import rmtree
from uuid import UUID, uuid4

import grpc

from figurative_server import figurative_server
from figurative_server.FigurativeServer_pb2 import *
from tests.mock_classes import MockContext


class FigurativeServerCoreNativeTest(unittest.TestCase):
    def setUp(self):
        this_dir = Path(getframeinfo(currentframe()).filename).resolve().parent
        self.dirname = str(this_dir)
        self.binary_path = str(
            this_dir.parent.parent
            / "tests"
            / "native"
            / "binaries"
            / "arguments_linux_amd64"
        )
        print(self.binary_path)
        self.test_event = threading.Event()
        self.servicer = figurative_server.FigurativeServicer(self.test_event)
        self.context = MockContext()

    def tearDown(self):
        for mwrapper in self.servicer.figurative_instances.values():
            mwrapper.figurative_object.kill()
            stime = time.time()
            while mwrapper.thread.is_alive():
                time.sleep(1)
                if (time.time() - stime) > 15:
                    break

    @classmethod
    def tearDownClass(cls):
        for f in glob.glob("mcore_*"):
            if Path(f).is_dir():
                rmtree(f, ignore_errors=True)

    def test_start_with_no_or_invalid_binary_path(self):
        self.servicer.StartNative(NativeArguments(), self.context)

        self.assertEquals(self.context.code, grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEquals(self.context.details, "Basic arguments are invalid!")

        self.context.reset()

        invalid_binary_path = str(
            self.dirname / Path("binaries") / Path("invalid_binary")
        )

        self.servicer.StartNative(
            NativeArguments(program_path=invalid_binary_path), self.context
        )

        self.assertEquals(self.context.code, grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEquals(self.context.details, "Basic arguments are invalid!")

    def test_start(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )

        try:
            UUID(mcore_instance.uuid)
        except ValueError:
            self.fail(
                "Start() returned FigurativeInstance with missing or malformed UUID"
            )

        self.assertTrue(mcore_instance.uuid in self.servicer.figurative_instances)

        mcore = self.servicer.figurative_instances[mcore_instance.uuid].figurative_object
        self.assertTrue(Path(mcore.workspace).is_dir())

    def test_start_with_find_avoid_hooks(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(
                program_path=str(self.binary_path),
                hooks=[
                    Hook(type=Hook.HookType.FIND, address=0x40100C),
                    Hook(type=Hook.HookType.AVOID, address=0x401018),
                ],
            ),
            self.context,
        )
        self.assertTrue(mcore_instance.uuid in self.servicer.figurative_instances)
        # TODO: Once logging is improved, check that find_f outputs successful stdin. Might require different test binary.

    def test_start_with_global_hook(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(
                program_path=str(self.binary_path),
                hooks=[
                    Hook(
                        type=Hook.HookType.GLOBAL,
                        func_text="\n".join(
                            (
                                "global m",
                                "def hook(state):",
                                "    m.test_attribute = True",
                                "    m.kill()",
                                "m.hook(None)(hook)",
                            )
                        ),
                    ),
                ],
            ),
            self.context,
        )

        self.assertTrue(mcore_instance.uuid in self.servicer.figurative_instances)
        m = self.servicer.figurative_instances[mcore_instance.uuid].figurative_object

        stime = time.time()
        while not hasattr(m, "test_attribute"):
            if (time.time() - stime) > 10:
                self.fail(
                    f"Global hook failed to trigger on {mcore_instance.uuid} before timeout"
                )
            time.sleep(1)

        self.assertTrue(m.test_attribute)

    def test_start_with_custom_hook(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(
                program_path=str(self.binary_path),
                hooks=[
                    Hook(
                        type=Hook.HookType.CUSTOM,
                        func_text="\n".join(
                            (
                                "global m, addr",
                                "def hook(state):",
                                "    m.test_attribute = addr",
                                "    m.kill()",
                                "m.hook(addr)(hook)",
                            )
                        ),
                        address=0x400FDC,
                    ),
                ],
            ),
            self.context,
        )

        self.assertTrue(mcore_instance.uuid in self.servicer.figurative_instances)
        m = self.servicer.figurative_instances[mcore_instance.uuid].figurative_object

        stime = time.time()
        while not hasattr(m, "test_attribute"):
            if (time.time() - stime) > 10:
                self.fail(
                    f"Custom hook failed to trigger on {mcore_instance.uuid} before timeout"
                )
            time.sleep(1)

        self.assertTrue(m.test_attribute == 0x400FDC)

    def test_start_with_invalid_custom_and_global_hook(self):

        self.servicer.StartNative(
            NativeArguments(
                program_path=str(self.binary_path),
                hooks=[
                    Hook(
                        type=Hook.HookType.CUSTOM,
                        func_text="this is an invalid hook",
                        address=0x400FDC,
                    ),
                ],
            ),
            self.context,
        )

        self.assertEquals(self.context.code, grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEquals(self.context.details, "Hooks set are invalid!")

        self.context.reset()

        self.servicer.StartNative(
            NativeArguments(
                program_path=str(self.binary_path),
                hooks=[
                    Hook(
                        type=Hook.HookType.GLOBAL,
                        func_text="this is another invalid hook",
                    ),
                ],
            ),
            self.context,
        )

        self.assertEquals(self.context.code, grpc.StatusCode.INVALID_ARGUMENT)
        self.assertEquals(self.context.details, "Hooks set are invalid!")

    def test_terminate_running_figurative(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        stime = time.time()
        while not mwrapper.figurative_object.is_running():
            if (time.time() - stime) > 5:
                self.fail(
                    f"Figurative instance {mcore_instance.uuid} failed to start running before timeout"
                )
            time.sleep(1)

        self.context.reset()

        self.servicer.Terminate(mcore_instance, self.context)
        self.assertEqual(self.context.code, grpc.StatusCode.OK)
        self.assertTrue(mwrapper.figurative_object.is_killed())

        stime = time.time()
        while mwrapper.figurative_object.is_running():
            if (time.time() - stime) > 10:
                self.fail(
                    f"Figurative instance {mcore_instance.uuid} failed to stop running before timeout"
                )
            time.sleep(1)

    def test_terminate_killed_figurative(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]
        mwrapper.figurative_object.kill()
        stime = time.time()
        while mwrapper.figurative_object.is_running():
            if (time.time() - stime) > 10:
                self.fail(
                    f"Figurative instance {mcore_instance.uuid} failed to stop running before timeout"
                )
            time.sleep(1)

        t_status = self.servicer.Terminate(mcore_instance, self.context)

        self.assertEquals(self.context.code, grpc.StatusCode.OK)

    def test_terminate_invalid_figurative(self):
        t_status = self.servicer.Terminate(
            FigurativeInstance(uuid=uuid4().hex), self.context
        )
        self.assertEqual(self.context.code, grpc.StatusCode.FAILED_PRECONDITION)

    def test_get_message_list_running_figurative(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        stime = time.time()
        while mwrapper.figurative_object._log_queue.empty() and time.time() - stime < 5:
            time.sleep(1)
            if not mwrapper.figurative_object._log_queue.empty():
                deque_messages = list(mwrapper.figurative_object._log_queue)
                messages = self.servicer.GetMessageList(
                    mcore_instance, self.context
                ).messages
                for i in range(len(messages)):
                    self.assertEqual(messages[i].content, deque_messages[i])
                break

    def test_get_message_list_stopped_figurative(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        mwrapper.figurative_object.kill()
        stime = time.time()
        while mwrapper.figurative_object.is_running():
            if (time.time() - stime) > 10:
                self.fail(
                    f"Figurative instance {mcore_instance.uuid} failed to stop running before timeout"
                )
            time.sleep(1)

        stime = time.time()
        while mwrapper.figurative_object._log_queue.empty() and time.time() - stime < 5:
            time.sleep(1)
            if not mwrapper.figurative_object._log_queue.empty():
                deque_messages = list(mwrapper.figurative_object._log_queue)
                messages = self.servicer.GetMessageList(
                    mcore_instance, self.context
                ).messages
                for i in range(len(messages)):
                    self.assertEqual(messages[i].content, deque_messages[i])
                break

    def test_get_message_list_invalid_figurative(self):
        message_list = self.servicer.GetMessageList(
            FigurativeInstance(uuid=uuid4().hex), self.context
        )
        self.assertEqual(self.context.code, grpc.StatusCode.FAILED_PRECONDITION)
        self.assertEqual(
            self.context.details, "Specified Figurative instance not found!"
        )
        self.assertEqual(len(message_list.messages), 0)

    def test_get_state_list_running_figurative(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        for i in range(5):
            time.sleep(1)
            state_list = self.servicer.GetStateList(mcore_instance, self.context)
            all_states = list(
                map(
                    lambda x: x.state_id,
                    list(state_list.active_states)
                    + list(state_list.waiting_states)
                    + list(state_list.forked_states)
                    + list(state_list.errored_states)
                    + list(state_list.complete_states),
                )
            )
            state_ids = mwrapper.figurative_object.introspect().keys()

            for sid in state_ids:
                self.assertIn(sid, all_states)

    def test_get_state_list_stopped_figurative(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        mwrapper.figurative_object.kill()
        stime = time.time()
        while mwrapper.figurative_object.is_running():
            if (time.time() - stime) > 10:
                self.fail(
                    f"Figurative instance {mcore_instance.uuid} failed to stop running before timeout"
                )
            time.sleep(1)

        stime = time.time()
        for i in range(5):
            time.sleep(1)
            state_list = self.servicer.GetStateList(mcore_instance, self.context)
            all_states = list(
                map(
                    lambda x: x.state_id,
                    list(state_list.active_states)
                    + list(state_list.waiting_states)
                    + list(state_list.forked_states)
                    + list(state_list.errored_states)
                    + list(state_list.complete_states),
                )
            )
            state_ids = mwrapper.figurative_object.introspect().keys()

            for sid in state_ids:
                self.assertIn(sid, all_states)

    def test_get_state_list_invalid_figurative(self):
        state_list = self.servicer.GetStateList(
            FigurativeInstance(uuid=uuid4().hex), self.context
        )

        self.assertFalse(state_list.active_states)
        self.assertFalse(state_list.waiting_states)
        self.assertFalse(state_list.forked_states)
        self.assertFalse(state_list.errored_states)
        self.assertFalse(state_list.complete_states)

    def test_check_figurative_running(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        stime = time.time()
        while not mwrapper.figurative_object.is_running():
            if (time.time() - stime) > 10:
                self.fail(
                    f"Figurative instance {mcore_instance.uuid} failed to start running before timeout"
                )
            time.sleep(1)

        self.assertTrue(
            self.servicer.CheckFigurativeRunning(mcore_instance, self.context).is_running
        )

        mwrapper.figurative_object.kill()

        stime = time.time()
        while mwrapper.thread.is_alive():
            if (time.time() - stime) > 45:
                self.fail(
                    f"Figurative instance {mcore_instance.uuid} failed to stop running and finish generating reports before timeout"
                )
            time.sleep(1)

        self.assertFalse(
            self.servicer.CheckFigurativeRunning(mcore_instance, self.context).is_running
        )

    def test_check_figurative_running_invalid_figurative(self):
        self.assertFalse(
            self.servicer.CheckFigurativeRunning(
                FigurativeInstance(uuid=uuid4().hex), self.context
            ).is_running
        )

    def test_control_state_invalid_figurative(self):
        self.servicer.ControlState(
            ControlStateRequest(
                figurative_instance=FigurativeInstance(uuid=uuid4().hex),
                state_id=1,
                action=ControlStateRequest.StateAction.PAUSE,
            ),
            self.context,
        )
        self.assertEqual(self.context.code, grpc.StatusCode.FAILED_PRECONDITION)
        self.assertEqual(
            self.context.details, "Specified Figurative instance not found!"
        )

    def test_control_state_invalid_state(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )

        self.servicer.ControlState(
            ControlStateRequest(
                figurative_instance=mcore_instance,
                state_id=-1,
                action=ControlStateRequest.StateAction.PAUSE,
            ),
            self.context,
        )
        self.assertEqual(self.context.code, grpc.StatusCode.FAILED_PRECONDITION)
        self.assertEqual(self.context.details, "Specified state not found!")

    def test_control_state_pause_state(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        stime = time.time()
        active_states = self.servicer.GetStateList(
            mcore_instance, self.context
        ).active_states
        while len(active_states) == 0:
            time.sleep(1)
            if (time.time() - stime) > 30:
                self.fail("Figurative did not create an active state before timeout")
            active_states = self.servicer.GetStateList(
                mcore_instance, self.context
            ).active_states
        candidate_state_id = list(active_states)[0].state_id

        self.servicer.ControlState(
            ControlStateRequest(
                figurative_instance=mcore_instance,
                state_id=candidate_state_id,
                action=ControlStateRequest.StateAction.PAUSE,
            ),
            self.context,
        )
        self.assertEqual(self.context.code, grpc.StatusCode.OK)
        self.assertEqual(self.context.details, "")

        self.assertTrue(candidate_state_id in mwrapper.paused_states)
        self.assertTrue(-1 in mwrapper.figurative_object._busy_states)
        stime = time.time()
        paused_states = self.servicer.GetStateList(
            mcore_instance, self.context
        ).paused_states
        while len(paused_states) == 0:
            time.sleep(1)
            if (time.time() - stime) > 30:
                self.fail(
                    f"Figurative did not pause the state {candidate_state_id} before timeout"
                )
            paused_states = self.servicer.GetStateList(
                mcore_instance, self.context
            ).paused_states
        self.assertTrue(candidate_state_id == list(paused_states)[0].state_id)

    def test_control_state_resume_paused_state(self):
        self.test_control_state_pause_state()
        self.assertTrue(len(self.servicer.figurative_instances) == 1)

        mwrapper = list(self.servicer.figurative_instances.values())[0]
        paused_state_id = list(mwrapper.paused_states)[0]

        self.servicer.ControlState(
            ControlStateRequest(
                figurative_instance=FigurativeInstance(uuid=mwrapper.uuid),
                state_id=paused_state_id,
                action=ControlStateRequest.StateAction.RESUME,
            ),
            self.context,
        )

        self.assertEqual(self.context.code, grpc.StatusCode.OK)
        self.assertEqual(self.context.details, "")

        self.assertTrue(len(mwrapper.paused_states) == 0)
        self.assertTrue(-1 not in mwrapper.figurative_object._busy_states)

        self.assertTrue(
            paused_state_id
            not in map(
                lambda x: x.state_id,
                self.servicer.GetStateList(
                    FigurativeInstance(uuid=mwrapper.uuid), self.context
                ).paused_states,
            )
        )

    def test_control_state_kill_active_state(self):
        mcore_instance = self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        mwrapper = self.servicer.figurative_instances[mcore_instance.uuid]

        stime = time.time()
        active_states = self.servicer.GetStateList(
            mcore_instance, self.context
        ).active_states
        while len(active_states) == 0:
            time.sleep(1)
            if (time.time() - stime) > 30:
                self.fail("Figurative did not create an active state before timeout")
            active_states = self.servicer.GetStateList(
                mcore_instance, self.context
            ).active_states
        candidate_state_id = list(active_states)[0].state_id

        self.servicer.ControlState(
            ControlStateRequest(
                figurative_instance=mcore_instance,
                state_id=candidate_state_id,
                action=ControlStateRequest.StateAction.KILL,
            ),
            self.context,
        )
        self.assertEqual(self.context.code, grpc.StatusCode.OK)
        self.assertEqual(self.context.details, "")

        stime = time.time()
        active_states = self.servicer.GetStateList(
            mcore_instance, self.context
        ).active_states
        while len(active_states) != 0:
            time.sleep(1)
            if (time.time() - stime) > 30:
                self.fail(
                    f"Figurative did not kill the state {candidate_state_id} before timeout"
                )
            active_states = self.servicer.GetStateList(
                mcore_instance, self.context
            ).active_states

    def test_control_state_kill_paused_state(self):
        self.test_control_state_pause_state()
        self.assertTrue(len(self.servicer.figurative_instances) == 1)

        mwrapper = list(self.servicer.figurative_instances.values())[0]
        paused_state_id = list(mwrapper.paused_states)[0]

        self.servicer.ControlState(
            ControlStateRequest(
                figurative_instance=FigurativeInstance(uuid=mwrapper.uuid),
                state_id=paused_state_id,
                action=ControlStateRequest.StateAction.KILL,
            ),
            self.context,
        )

        self.assertEqual(self.context.code, grpc.StatusCode.OK)
        self.assertEqual(self.context.details, "")

        self.assertTrue(len(mwrapper.paused_states) == 0)
        self.assertTrue(-1 not in mwrapper.figurative_object._busy_states)

        self.assertTrue(
            paused_state_id
            not in map(
                lambda x: x.state_id,
                self.servicer.GetStateList(
                    FigurativeInstance(uuid=mwrapper.uuid), self.context
                ).paused_states,
            )
        )

    def test_stop_server(self):
        self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )
        self.servicer.StartNative(
            NativeArguments(program_path=self.binary_path), self.context
        )

        self.servicer.StopServer(StopServerRequest(), self.context)

        self.assertTrue(self.test_event.is_set())
        for mwrapper in self.servicer.figurative_instances.values():
            self.assertFalse(mwrapper.figurative_object.is_running())
